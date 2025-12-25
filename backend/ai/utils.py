import json
import math
import re
import base64
import time
import logging
from typing import Iterable, List, Optional

import requests
import urllib3
# SSL 경고 무시
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from django.conf import settings
from django.core.files.base import ContentFile
from django.db.models import Q 

# 로깅 설정
logger = logging.getLogger(__name__)

# SSAFY GMS 프록시 주소
GEMINI_BASE_URL = "https://gms.ssafy.io/gmsapi/generativelanguage.googleapis.com"


# =========================================================
# [1] 공통 유틸리티 함수
# =========================================================
def _strip_code_fence(s: str) -> str:
    """마크다운 코드 블록(```json 등) 제거"""
    if not s: return s
    s = s.strip()
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```$", "", s)
    return s.strip()

def _strip_wrapping_quotes(s: str) -> str:
    """문자열 앞뒤 따옴표 제거"""
    s = (s or "").strip()
    if len(s) >= 2 and ((s[0] == s[-1] == '"') or (s[0] == s[-1] == "'")):
        return s[1:-1].strip()
    return s

def _extract_json(text: str):
    """AI 응답 텍스트에서 JSON 객체 추출"""
    if not text: return None
    t = _strip_code_fence(text)
    try: return json.loads(t)
    except Exception: pass
    
    # JSON처럼 생긴 부분 찾기 ({...} 또는 [...])
    m = re.search(r"(\[[\s\S]*?\]|\{[\s\S]*?\})", t)
    if not m: return None
    candidate = m.group(1).strip()
    # 혹시 모를 trailing comma 제거
    candidate = re.sub(r",\s*([\]}])", r"\1", candidate)
    try: return json.loads(candidate)
    except Exception: return None

def _normalize_space(s: str) -> str:
    """줄바꿈을 공백으로 치환하고 다중 공백 제거"""
    s = (s or "").replace("\n", " ").strip()
    s = re.sub(r"\s+", " ", s)
    return s.strip()


# =========================================================
# [2] 불용어 및 검색어 처리
# =========================================================
STOPWORDS = {
    "추천", "해줘", "해주세요", "좋은", "요즘", "최근", "많이", "위주", "느낌",
    "책", "도서", "소설", "읽을", "읽고", "읽어", "싶어", "원해", "원합니다",
    "장르", "분위기", "재밌는", "재미있는", "재미", "베스트셀러",
    "대한", "관련", "관한", "위한", "고민", "걱정", "생각", "많아", "좀", "약간",
    "내용", "줄거리", "주제", "알려줘", "찾아줘", "소개", "목록", "비슷한",
    "무슨", "어떤", "것", "등", "나오는", "있는"
}

def extract_keywords_fallback(text: str, *, limit: int = 8) -> list[str]:
    """단순 형태소 분석 느낌으로 단어 추출 (Fallback용)"""
    tokens = re.findall(r"[가-힣A-Za-z0-9]{2,}", (text or "").lower())
    out: list[str] = []
    for t in tokens:
        if t in STOPWORDS: continue
        if t not in out: out.append(t)
        if len(out) >= limit: break
    return out

def build_keyword_filter_q(keywords: list[str]) -> Q:
    """키워드 리스트로 Django Q 필터 생성"""
    q = Q()
    for kw in keywords:
        q |= Q(title__icontains=kw)
        q |= Q(description__icontains=kw)
        q |= Q(category__name__icontains=kw)
        q |= Q(publisher__icontains=kw)
    return q


# =========================================================
# [3] Gemini API 호출 (텍스트 생성) - 타임아웃 적용
# =========================================================
def _gemini_generate_text(prompt: str, *, force_json: bool = True) -> str:
    """Gemini Pro 모델 호출"""
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    model = getattr(settings, "GEMINI_MODEL", "gemini-2.5-flash")
    if not api_key: raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

    url = f"{GEMINI_BASE_URL}/v1beta/models/{model}:generateContent?key={api_key}"
    generation_config = {"temperature": 0.3, "topP": 0.8, "topK": 40, "maxOutputTokens": 800}
    if force_json: generation_config["responseMimeType"] = "application/json"

    payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": generation_config}
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}

    try:
        # [타임아웃 설정] 연결 5초, 응답 30초
        resp = requests.post(url, json=payload, headers=headers, timeout=(5, 30), verify=False)
        resp.raise_for_status() 
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        logger.error(f"Gemini API Error: {e}")
        return "" # 실패 시 빈 문자열 반환

def build_user_preference_text(v: dict) -> str:
    """사용자 요청 딕셔너리를 하나의 문장으로 요약"""
    lines = [f"- 자유요청: {v.get('prompt', '')}"]
    if v.get("mood"): lines.append(f"- 분위기: {v['mood']}")
    themes = v.get("themes") or []
    if themes: lines.append(f"- 원하는 주제/요소: {', '.join(themes)}")
    length = v.get("length")
    if length: lines.append(f"- 분량 선호: {length}")
    return "\n".join(lines).strip()


# =========================================================
# [4] 사용자 의도 파악 (문장 이해력 강화)
# =========================================================
def extract_intent_json(user_prompt: str) -> dict:
    p = (user_prompt or "").strip()
    
    # [수정] 프롬프트를 개선하여 '문장'의 의미를 해석하도록 유도
    prompt = (
        "너는 최고의 도서 검색 전문가다.\n"
        "사용자가 입력한 문장의 '속뜻'과 '핵심 감정', '상황'을 파악해라.\n"
        f"[사용자 입력]: \"{p}\"\n\n"
        "다음 JSON 형식으로만 출력해라 (설명 금지):\n"
        "{\n"
        "  \"intent\": \"사용자의 의도를 한 문장으로 요약 (예: 위로가 필요한 상황에서 읽기 편한 에세이 요청)\",\n"
        "  \"core_topics\": [\"핵심 키워드1\", \"키워드2\", \"키워드3\"],\n"
        "  \"mood\": \"분위기 (예: 따뜻한, 우울한, 진지한)\",\n"
        "  \"request_type\": \"요청유형\",\n"
        "  \"avoid\": [\"피하고 싶은 것\"],\n"
        "  \"notes\": \"기타 특이사항\"\n"
        "}\n\n"
        "규칙:\n"
        "1. 사용자가 '설명'을 했다면 그 상황에 어울리는 '추상적 키워드'를 뽑아라. (예: '회사 가기 싫어' -> '번아웃', '힐링', '직장인')\n"
        "2. '책', '추천', '해줘' 같은 불용어는 키워드에서 절대 제외해라."
    )

    raw = _gemini_generate_text(prompt, force_json=True)
    if not raw: return {} # 에러 시 빈 딕셔너리 반환

    data = _extract_json(raw)
    if not isinstance(data, dict): data = {}

    # 결과 데이터 정제
    core = data.get("core_topics") or []
    filtered_core = []
    for t in core:
        t_clean = str(t).strip()
        if t_clean in STOPWORDS: continue
        if t_clean.endswith("관련"): t_clean = t_clean[:-2]
        if t_clean and t_clean not in STOPWORDS: filtered_core.append(t_clean)
    data["core_topics"] = filtered_core

    if not data["core_topics"] and p:
        cleaned_p = p.replace("추천", "").replace("해줘", "").strip()
        if cleaned_p: data["core_topics"] = [cleaned_p[:10]]

    if not isinstance(data.get("avoid"), list): data["avoid"] = []
    return data


# =========================================================
# [5] 텍스트 임베딩 (벡터 검색용)
# =========================================================
def _sanitize_text(s: str, max_chars: int) -> str:
    s = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", " ", (s or ""))
    return re.sub(r"\s+", " ", s).strip()[:max_chars]

def gemini_embed_text(text: str, *, task_type="RETRIEVAL_QUERY", title=None) -> List[float]:
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    model = getattr(settings, "GEMINI_EMBED_MODEL", "text-embedding-004")
    if not api_key: raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

    url = f"{GEMINI_BASE_URL}/v1beta/models/{model}:embedContent?key={api_key}"
    payload = {"content": {"parts": [{"text": _sanitize_text(text, 2500)}]}}
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=(5, 10), verify=False)
        if resp.status_code != 200: 
            return []
        return resp.json()["embedding"]["values"]
    except Exception as e:
        logger.error(f"Embedding Exception: {e}")
        return []

def gemini_batch_embed_texts(texts: List[str], *, _depth: int = 0) -> List[List[float]]:
    if not texts: return []
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    model = getattr(settings, "GEMINI_EMBED_MODEL", "text-embedding-004")
    if not api_key: raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

    max_text_chars = int(getattr(settings, "AI_MAX_EMBED_CHARS", 2500))
    safe_texts = [_sanitize_text(t, max_text_chars) for t in texts]

    url = f"{GEMINI_BASE_URL}/v1beta/models/{model}:batchEmbedContents?key={api_key}"
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}
    payload = {"requests": [{"model": f"models/{model}", "content": {"parts": [{"text": t}]}} for t in safe_texts]}

    try:
        resp = requests.post(url, json=payload, headers=headers, timeout=(10, 60), verify=False)
        if resp.status_code != 200:
            if _depth >= 3: return [[] for _ in texts]
            mid = len(texts) // 2
            left = gemini_batch_embed_texts(texts[:mid], _depth=_depth + 1)
            right = gemini_batch_embed_texts(texts[mid:], _depth=_depth + 1)
            return left + right

        data = resp.json()
        embeddings = data.get("embeddings") or []
        return [e.get("values", []) for e in embeddings]
    except Exception as e:
        logger.error(f"Batch Embed Exception: {e}")
        return [[] for _ in texts]

def vector_norm(v: Iterable[float]) -> float:
    return math.sqrt(sum((x * x) for x in v))

def cosine_similarity(a: List[float], b: List[float], *, norm_a=None, norm_b=None) -> float:
    if not a or not b or len(a) != len(b): return -1.0
    na = norm_a or vector_norm(a)
    nb = norm_b or vector_norm(b)
    if na == 0 or nb == 0: return -1.0
    return sum(x*y for x,y in zip(a,b)) / (na * nb)

def build_book_document_text(book) -> str:
    cat = book.category.name if getattr(book, "category", None) else ""
    desc = (book.description or "").replace("\n", " ").strip()
    return f"제목: {book.title}\n저자: {getattr(book,'author','')}\n분류: {cat}\n소개: {desc}"

def ensure_book_embedding(book, *, force: bool = False):
    from ai.models import BookEmbedding
    obj, _ = BookEmbedding.objects.get_or_create(book=book)
    if obj.embedding and obj.embedding_norm and not force:
        return obj.embedding, float(obj.embedding_norm)
    
    emb = gemini_embed_text(build_book_document_text(book))
    if not emb: return [], 0.0

    n = vector_norm(emb)
    obj.embedding = emb
    obj.embedding_norm = n
    obj.embedding_model = getattr(settings, "GEMINI_EMBED_MODEL", "text-embedding-004")
    obj.save()
    return emb, n


# =========================================================
# [6] 추천 사유 생성 (형식 준수 및 길이 제한 강화)
# =========================================================

def _trim_to_sentence_end(s: str, max_len: int = 250) -> str:
    """주어진 길이 근처에서 문장이 끝나도록 자름"""
    s = _normalize_space(s)
    if len(s) <= max_len:
        return s
    
    truncated = s[:max_len]
    match = list(re.finditer(r'[.!?](?:\s|$)', truncated))
    
    if match:
        last_match = match[-1]
        return truncated[:last_match.end()].strip()
    else:
        return truncated.strip() + "..."

# Fallback용 기본 멘트
def heuristic_reason(*, book, user_keywords: List[str], mood: Optional[str], themes: List[str]) -> str:
    cat = book.category.name if getattr(book, "category", None) else "이 분야"
    return f"'{book.title}'은 {cat} 분야의 수작으로, 요청하신 주제에 대해 깊이 있는 통찰을 제공합니다. 이 책을 통해 새로운 관점을 얻으실 수 있을 거예요."

def generate_reason_for_book(*, user_pref_text, user_keywords, mood, themes, book, match_keywords) -> str:
    cat_name = book.category.name if getattr(book, "category", None) else ""
    desc = (book.description or "").replace("\n", " ").strip()
    desc = desc[:400]

    # [수정] 프롬프트 강화: 큐레이터 페르소나, 형식 강제, 길이 제한
    prompt = (
        "당신은 서점의 다정하고 식견 넓은 'AI 큐레이터'입니다.\n"
        "손님(사용자)의 상황에 맞춰 이 책을 추천하는 **정성스러운 추천사**를 작성해주세요.\n\n"
        f"[사용자 요청]: \"{user_pref_text}\"\n"
        f"[책 제목]: {book.title}\n"
        f"[책 내용]: {desc}\n\n"
        "★필수 출력 형식 (이 형식을 절대 지킬 것)★:\n"
        "이 책을 추천하는 이유는 분명합니다. (자연스러운 줄거리 요약 1~2문장). "
        "무엇보다 (사용자 상황)을 겪는 당신에게 (구체적인 위로/해결책/재미)를 줄 수 있기 때문입니다. "
        "꼭 한번 읽어보시길 바랍니다.\n\n"
        "★작성 규칙★:\n"
        "1. 말투: '~입니다/합니다' 존댓말 사용, 따뜻하고 공감하는 어조.\n"
        "2. **길이 제한**: 데이터베이스 저장을 위해 **공백 포함 250자 이내**로 핵심만 꽉 채워서 작성.\n"
        "3. 내용: 책 내용이 없으면 당신의 지식으로 줄거리를 채우고, 뻔한 말보다는 구체적인 감상을 적을 것."
    )

    try:
        raw = _gemini_generate_text(prompt, force_json=False)
        
        # AI 응답이 비었거나 오류면 에러 발생 -> Fallback으로 이동
        if not raw: 
            raise ValueError("AI response is empty")

        txt = _strip_wrapping_quotes(_strip_code_fence(raw)).strip()
        
        # 250자 제한으로 자르기
        final_reason = _trim_to_sentence_end(txt, 250)
        
        if len(final_reason) < 30: 
            raise ValueError("Response too short")
            
        return final_reason

    except Exception as e:
        # 에러 발생 시(타임아웃 등) 서버 죽이지 말고 기본 멘트 반환
        logger.warning(f"Using Fallback for {book.title}: {e}")
        return heuristic_reason(book=book, user_keywords=user_keywords, mood=mood, themes=themes)


# =========================================================
# [7] Imagen 4.0 4컷 만화 생성 (타임아웃 방지 적용)
# =========================================================
def generate_comic_image_file(book_title: str, book_summary: str) -> ContentFile:
    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not api_key: raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

    url = f"{GEMINI_BASE_URL}/v1beta/models/imagen-4.0-generate-001:predict"

    # [단계 1] 시나리오 생성
    scenario_prompt = (
        "You are a visual storyteller. I need a description for a 4-panel comic strip about the book.\n"
        f"Book Title: {book_title}\n"
        f"Summary: {book_summary[:500]}\n"
        "Task:\n"
        "1. Create a visual description for 4 panels.\n"
        "2. Output ONLY the English description."
    )
    
    enriched_description = _gemini_generate_text(scenario_prompt, force_json=False)
    if not enriched_description:
        enriched_description = f"Comic about {book_title}. {book_summary}"

    # [단계 2] Imagen 요청
    prompt_text = (
        f"Create a high-quality 4-panel comic strip based on this description:\n{enriched_description[:800]}\n\n"
        "Style & Constraints:\n"
        "- Webtoon / Manhwa style, colorful.\n"
        "- **STRICTLY SILENT COMIC (NO TEXT)**: No bubbles/text.\n"
        "- Clear division between 4 panels."
    )

    payload = {
        "instances": [{"prompt": prompt_text}],
        "parameters": {"sampleCount": 1}
    }
    headers = {"Content-Type": "application/json", "x-goog-api-key": api_key}

    logger.info(f"Imagen Request for: {book_title}")

    try:
        # 이미지 생성 타임아웃 50초
        resp = requests.post(url, json=payload, headers=headers, timeout=50, verify=False)
        if resp.status_code != 200:
            raise ValueError(f"Imagen API 실패 ({resp.status_code}): {resp.text}")

        data = resp.json()
        b64_data = data["predictions"][0]["bytesBase64Encoded"]
        img_content = base64.b64decode(b64_data)
        file_name = f"comic_{int(time.time())}.png"
        return ContentFile(img_content, name=file_name)
    except Exception as e:
        logger.error(f"Imagen Gen Failed: {e}")
        raise ValueError(f"이미지 생성 중 통신 에러: {e}")
