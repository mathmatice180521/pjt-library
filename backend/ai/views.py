import logging
import re
import time # [추가] 파일명 타임스탬프용

# [추가] 파일 저장 및 API 응답 관련
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from rest_framework.decorators import api_view, permission_classes

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from books.models import Book
from interactions.models import Bookmark

from .models import AIRecommendation, AIRecommendationItem, AIContent
from .serializers import AIRecommendationSerializer, AIRecommendRequestSerializer

# [수정] utils.py에 정의된 함수들을 모두 불러옵니다. (ImportError 해결)
from .utils import (
    build_user_preference_text,
    cosine_similarity,
    ensure_book_embedding,
    extract_intent_json,
    gemini_embed_text,
    generate_reason_for_book,
    # [추가] 만화 생성 함수
    generate_comic_image_file,
    # [추가] utils로 이동한 fallback 함수들
    extract_keywords_fallback,
    build_keyword_filter_q, 
)

logger = logging.getLogger(__name__)


# =========================================================
# [수정 전] utils.py로 이동된 함수들 주석 처리
# 이유: utils.py에서 임포트하여 사용하므로 중복 정의 제거
# =========================================================
# STOPWORDS = { ... }
# def extract_keywords_fallback(...): ...
# def build_keyword_filter_q(...): ...


def _pub_sort_value(bk) -> int:
    pd = getattr(bk, "pub_date", None)
    if not pd:
        return 0
    try:
        return int(pd.toordinal())
    except Exception:
        try:
            return int(pd.timestamp())
        except Exception:
            return 0


def pick_candidates_by_keyword_score(qs, keywords: list[str], *, base_limit: int = 300, final_limit: int = 20):
    """
    임베딩이 없거나 embed 실패 시 fallback 랭킹
    """
    base = list(qs.order_by("-customer_review_rank", "-pub_date")[:base_limit])
    if not keywords:
        return base[:final_limit]

    def score_book(bk) -> int:
        cat = bk.category.name if getattr(bk, "category", None) else ""
        txt = f"{bk.title} {bk.author} {bk.publisher} {cat} {bk.description or ''}".lower()
        return sum(1 for kw in keywords if kw and kw.lower() in txt)

    base.sort(
        key=lambda bk: (
            score_book(bk),
            bk.customer_review_rank or 0,
            _pub_sort_value(bk),
        ),
        reverse=True,
    )
    return base[:final_limit]


# =========================================================
# [추가] 4컷 만화 생성 View
# =========================================================
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_comic_view(request, book_id):
    """
    [B안] 특정 책(book_id)에 대한 4컷 만화 생성 API
    - 이미 생성된 게 있으면 DB URL 반환
    - 없으면 Imagen 호출 -> media 저장 -> URL 반환
    """
    try:
        book = Book.objects.get(pk=book_id)
    except Book.DoesNotExist:
        return Response({"error": "책을 찾을 수 없습니다."}, status=404)

    # 1. 이미 생성된 컨텐츠가 있는지 확인
    ai_content, created = AIContent.objects.get_or_create(book=book)
    
    # 이미 URL이 존재하면 새로 만들지 않고 반환 (비용 절약)
    if ai_content.comic_image_url:
        return Response({
            "book_id": book.id,
            "comic_url": ai_content.comic_image_url,
            "message": "이미 생성된 만화가 있어 반환합니다."
        })

    # 2. 이미지 생성 (시간 소요됨)
    try:
        # 요약 텍스트가 없으면 책 소개글 사용
        summary = ai_content.summary_text or book.description or "재미있는 이야기"
        
        # utils.py의 함수 호출하여 이미지 파일 객체(ContentFile) 획득
        image_file = generate_comic_image_file(book.title, summary)
        
        # 3. 파일 저장 (Media 폴더)
        # 파일명 생성: comics/comic_{book_id}_{timestamp}.png
        file_name = f"comics/comic_{book.id}_{int(time.time())}.png"
        file_path = default_storage.save(file_name, image_file)
        
        # 4. URL 생성 (로컬이면 /media/..., S3면 https://...)
        full_url = default_storage.url(file_path)
        
        # 5. DB 업데이트
        ai_content.comic_image_url = full_url
        ai_content.save()

        return Response({
            "book_id": book.id,
            "comic_url": full_url,
            "message": "새로운 만화가 생성되었습니다."
        })

    except Exception as e:
        # [디버깅] 구체적인 에러 내용을 로그에 남김
        logger.exception("만화 생성 실패")
        print(f"🔥 [View Error] 만화 생성 중 에러 발생: {e}")
        return Response({"error": str(e)}, status=500)


class AIRecommendView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        로그인 유저의 추천 히스토리 목록(여러 건) 조회
        """
        qs = (
            AIRecommendation.objects
            .filter(user=request.user)
            .prefetch_related("items__book")
            .order_by("-created_at")
        )

        total_count = qs.count()

        try:
            page = int(request.query_params.get("page", 1))
        except Exception:
            page = 1
        try:
            page_size = int(request.query_params.get("page_size", 10))
        except Exception:
            page_size = 10

        page = max(1, page)

        if page_size <= 0:
            recs = list(qs)
            data = AIRecommendationSerializer(recs, many=True).data
            return Response(
                {
                    "total_count": total_count,
                    "total_pages": 1 if total_count else 0,
                    "page": 1,
                    "page_size": total_count,
                    "results": data,
                },
                status=status.HTTP_200_OK,
            )

        page_size = max(1, page_size)
        total_pages = (total_count + page_size - 1) // page_size

        start = (page - 1) * page_size
        end = start + page_size

        recs = list(qs[start:end])
        data = AIRecommendationSerializer(recs, many=True).data

        return Response(
            {
                "total_count": total_count,
                "total_pages": total_pages,
                "page": page,
                "page_size": page_size,
                "results": data,
            },
            status=status.HTTP_200_OK,
        )


    def post(self, request):
        user = request.user

        # 0) 입력 검증
        req = AIRecommendRequestSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        v = req.validated_data

        prompt_text = (v.get("prompt") or "").strip()
        themes = v.get("themes") or []
        length = v.get("length")
        mood = v.get("mood")

        # 1) ✅ LLM 의도 추출(JSON)
        try:
            intent = extract_intent_json(prompt_text)
        except Exception as e:
            logger.exception("intent 추출 실패: %s", e)
            intent = {}

        core_topics = intent.get("core_topics") or []
        intent_line = intent.get("intent") or prompt_text
        request_type = intent.get("request_type")
        mood2 = intent.get("mood")
        avoid = intent.get("avoid") or []
        notes = intent.get("notes")

        if not mood and mood2:
            mood = mood2

        # intent가 빈약하면 fallback 키워드 사용 (utils 함수 호출)
        if not core_topics:
            core_topics = extract_keywords_fallback(prompt_text)

        # 2) 사용자 선호 텍스트
        user_pref_text = build_user_preference_text(v)

        # 3) 후보 풀 구성
        candidates_qs = Book.objects.select_related("category", "ai_embedding")

        # (A) 수험서/문제집 제거
        EXCLUDE_CATEGORY = ["수험", "자격", "공무원", "대학교재", "학습", "문제집"]
        EXCLUDE_TITLE = ["필기", "실기", "기출", "모의고사", "N제", "합격", "기사", "산업기사", "운전면허"]
        for kw in EXCLUDE_CATEGORY:
            candidates_qs = candidates_qs.exclude(category__name__icontains=kw)
        for kw in EXCLUDE_TITLE:
            candidates_qs = candidates_qs.exclude(title__icontains=kw)

        # (B) 라노벨/장르 트리거
        prompt_l = prompt_text.lower()
        manga_requested = any(k in prompt_l for k in ["만화", "웹툰", "코믹", "comic"])

        LN_TRIGGERS = ["라이트노벨", "라노벨", "ライトノベル", "하렘", "하렘물", "러브코미디", "이세계", "전생"]
        if any(k.lower() in prompt_l for k in LN_TRIGGERS) or any(t in core_topics for t in ["라이트노벨", "라노벨", "하렘", "이세계"]):
            ln_q = (
                Q(category__name__icontains="라이트") |
                Q(category__name__icontains="라노") |
                Q(category__name__icontains="판타지") |
                Q(category__name__icontains="소설") |
                Q(category__name__icontains="문학")
            )
            if manga_requested:
                ln_q |= Q(category__name__icontains="만화")
            candidates_qs = candidates_qs.filter(ln_q)

        # (C) 북마크 제외
        bookmarked_book_ids = Bookmark.objects.filter(user=user).values_list("book_id", flat=True)
        candidates_qs = candidates_qs.exclude(id__in=bookmarked_book_ids)

        # (D) core_topics로 약하게 필터링 (utils 함수 사용)
        if core_topics:
             filtered = candidates_qs.filter(build_keyword_filter_q(core_topics))
             if filtered.exists():
                 candidates_qs = filtered

        # 4) ✅ 임베딩 쿼리 구성
        embed_query = f"""
[의도] {intent_line}
[원문] {prompt_text}
[핵심토픽] {", ".join(core_topics[:6])}
""".strip()

        if request_type: embed_query += f"\n[원하는도움] {request_type}"
        if mood: embed_query += f"\n[분위기] {mood}"
        if themes: embed_query += "\n[원하는요소] " + ", ".join(themes[:6])
        if length: embed_query += f"\n[분량] {length}"
        if notes: embed_query += f"\n[제약] {notes}"
        if avoid: embed_query += "\n[피하고싶음] " + ", ".join([str(x) for x in avoid[:4]])

        # 5) 사용자 쿼리 임베딩
        try:
            query_embedding = gemini_embed_text(embed_query)
        except Exception as e:
            logger.exception("Gemini embedContent 실패: %s", e)
            query_embedding = None

        # 6) 임베딩 기반 스코어링
        scored = []
        lazy_limit = int(getattr(settings, "AI_EMBED_LAZY_LIMIT", 10))
        lazy_done = 0

        base_books = list(candidates_qs.order_by("-customer_review_rank", "-pub_date")[:250])

        if query_embedding:
            for bk in base_books:
                emb_obj = getattr(bk, "ai_embedding", None)

                if (not emb_obj) or (not emb_obj.embedding) or (not emb_obj.embedding_norm):
                    if lazy_done >= lazy_limit:
                        continue
                    try:
                        emb, emb_norm = ensure_book_embedding(bk, force=False)
                        lazy_done += 1
                    except Exception:
                        continue
                else:
                    emb = emb_obj.embedding
                    emb_norm = emb_obj.embedding_norm

                sim = cosine_similarity(query_embedding, emb, norm_b=emb_norm)
                if sim > -0.5:
                    scored.append((sim, bk))

        candidates: list[Book] = []
        if scored:
            scored.sort(
                key=lambda x: (
                    x[0],
                    x[1].customer_review_rank or 0,
                    _pub_sort_value(x[1]),
                ),
                reverse=True,
            )
            candidates = [bk for _, bk in scored[:20]]

        if not candidates:
            # 임베딩 실패시 fallback
            candidates = pick_candidates_by_keyword_score(candidates_qs, core_topics, base_limit=300, final_limit=20)

        top3 = candidates[:3]

        # 7) reason 생성
        picked = []
        for bk in top3:
            cat = bk.category.name if getattr(bk, "category", None) else ""
            txt = f"{bk.title} {bk.author} {bk.publisher} {cat} {bk.description or ''}".lower()
            match_topics = [kw for kw in core_topics if kw and kw.lower() in txt][:5]

            reason = generate_reason_for_book(
                user_pref_text=user_pref_text,
                user_keywords=core_topics,
                mood=mood,
                themes=themes,
                book=bk,
                match_keywords=match_topics,
            )

            picked.append({"book_pk": bk.id, "reason": reason})

        # 8) 저장
        with transaction.atomic():
            rec = AIRecommendation.objects.create(user=user)
            AIRecommendationItem.objects.bulk_create([
                AIRecommendationItem(
                    recommendation=rec,
                    book_id=item["book_pk"],
                    reason=item["reason"],
                )
                for item in picked
            ])

        rec = AIRecommendation.objects.filter(id=rec.id).prefetch_related("items__book").first()
        return Response(AIRecommendationSerializer(rec).data, status=status.HTTP_200_OK)