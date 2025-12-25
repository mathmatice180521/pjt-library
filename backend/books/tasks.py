import os
import re
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from .models import Book, Category


# .env 파일에서 환경변수 불러오기
load_dotenv()

# 알라딘 API 키
ALADIN_API_KEY = os.getenv("ALADIN_API_KEY")

# 1) 장르/분위기(소설/문학)
FICTION_QUERIES = [
    "소설", "단편", "장편", "시", "시집", "에세이",
    "사랑", "연애", "이별", "가족", "우정", "관계", "청춘", "성장", "일상", "비밀",
    "추리", "미스터리", "스릴러", "탐정", "사건", "살인", "범죄", "복수",
    "판타지", "마법", "용", "왕국", "모험", "전설",
    "SF", "우주", "미래", "로봇", "인공지능", "디스토피아",
    "공포", "괴담", "유령", "저주",
    "힐링", "위로", "눈물", "기적", "행복",
]

# 2) 인문/사회/교양
HUMANITIES_QUERIES = [
    "철학", "심리", "마음", "감정", "자존감", "불안", "우울", "행복", "관계",
    "역사", "세계사", "한국사", "전쟁", "혁명", "제국", "문명",
    "사회", "정치", "민주주의", "자본주의", "경제", "불평등",
    "인문학", "고전", "신화", "종교", "명상",
    "예술", "미술", "음악", "영화", "사진", "디자인",
]

# 3) 자기계발/라이프
LIFE_QUERIES = [
    "습관", "루틴", "목표", "성공", "몰입", "집중", "동기", "자기관리",
    "시간", "공부", "기억", "독서", "글쓰기",
    "소통", "대화", "말하기", "리더십", "협상",
    "정리", "미니멀", "청소", "정돈",
    "건강", "운동", "다이어트", "근력", "요가", "필라테스",
    "요리", "레시피", "집밥", "베이킹", "빵",
]

# 4) 비즈/재테크/커리어
BIZ_QUERIES = [
    "투자", "주식", "부동산", "경제", "돈", "자산", "파이어", "연금", "절약",
    "마케팅", "브랜딩", "전략", "기획", "창업", "스타트업",
    "회계", "재무", "면접", "이직", "커리어", "취업",
    "리더", "조직", "팀", "관리", "성과",
]

# 5) IT/개발/데이터/AI
TECH_QUERIES = [
    "파이썬", "자바", "자바스크립트", "리액트", "뷰", "장고", "스프링",
    "코딩", "알고리즘", "자료구조", "면접", "CS",
    "데이터", "SQL", "데이터분석", "머신러닝", "딥러닝", "인공지능", "LLM",
    "클라우드", "도커", "쿠버네티스", "리눅스", "네트워크", "보안",
]

# 6) 취미/실용/여행/음식/반려
HOBBY_QUERIES = [
    "여행", "지도", "산책", "캠핑", "등산", "바다", "제주", "부산", "일본", "유럽",
    "커피", "와인", "칵테일", "맥주", "디저트",
    "반려견", "강아지", "고양이", "식물", "가드닝",
    "그림", "드로잉", "수채화", "캘리그라피", "사진",
    "요리", "한식", "중식", "일식", "양식",
]

# 7) 어린이/청소년/학습
KIDS_QUERIES = [
    "어린이", "초등", "중등", "청소년",
    "과학", "수학", "영어", "한국사", "세계사",
    "동화", "그림책", "만화", "학습만화",
]

LN_QUERIES = [
    "라이트노벨", "라노벨", "ライトノベル",
    "전격문고", "MF문고J", "스니커문고", "GA문고", "HJ문고",
    "노블엔진", "노블엔진 POP", "J-Novel", "익스트림노벨",
    "키노의 여행", "사오", "소드 아트 온라인", "리제로", "Re:제로",
]

LN_COMMON_TITLE_QUERIES = [
    "이세계", "전생", "환생", "치트", "용사", "마왕", "던전", "길드",
    "연애", "러브코미디", "러브 코미디", "라브코메", "하이스쿨", "학원", "동아리",
    "선배", "후배", "여동생", "소꿉친구",
    "마법", "검", "소드", "기사", "왕녀", "공주", "성녀", "미궁",
    "스킬", "레벨", "랭크", "최강", "무쌍", "무쌍", "먼치킨",
    "헌터", "아카데미", "용병",
]

HAREM_STYLE_QUERIES = [
    # 직격
    "하렘", "후궁", "미소녀",
    # 라노벨 하렘 흔한 소재
    "여동생", "소꿉친구", "선배", "후배", "동거", "약혼", "혼약",
    "전학생", "학생회", "메이드", "집사",
    "사역마", "계약", "소환", "정령",
    "마왕", "용사", "성녀", "마법소녀",
    # 러브코메 쪽
    "러브코미디", "러브 코미디", "연애", "고백", "첫사랑", "삼각관계",
    # 제목에 자주 나오는 캐릭터 속성
    "츤데레", "얀데레", "멘헤라"
]

# 최종 기본 검색어 목록
DEFAULT_QUERIES = (
    FICTION_QUERIES
    + HUMANITIES_QUERIES
    + LIFE_QUERIES
    + BIZ_QUERIES
    + TECH_QUERIES
    + HOBBY_QUERIES
    + KIDS_QUERIES
    + LN_QUERIES
    + LN_COMMON_TITLE_QUERIES
    + HAREM_STYLE_QUERIES
)


def _upgrade_cover_url(url: str | None) -> str | None:
    """Return a higher-resolution cover URL when the source is Aladin."""
    if not url:
        return url
    if "image.aladin.co.kr" not in url:
        return url
    if "/cover500/" in url:
        return url

    # coversum(썸네일) / cover200(200px) / cover(기타) -> cover500
    return re.sub(r"/(coversum|cover200|cover)/", "/cover500/", url)

def get_books_from_aladin(query, max_results=50, start_index=1):
    url = "https://www.aladin.co.kr/ttb/api/ItemSearch.aspx"
    params = {
        "ttbkey": ALADIN_API_KEY,
        "Querytype": "Title",
        "Query": query,
        "MaxResults": max_results,
        "Start": start_index,
        "SearchTarget": "Book",
        "output": "JS",
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        response_text = response.text

        # 응답 본문에 여러 객체/문자열이 섞여 있을 수 있어 JSON만 잘라 파싱
        json_start = response_text.find("{")
        json_end = response_text.rfind("}")

        if json_start == -1 or json_end == -1:
            print("유효한 JSON 데이터를 찾을 수 없습니다.")
            return None

        valid_json = response_text[json_start : json_end + 1]

        try:
            return json.loads(valid_json)
        except json.JSONDecodeError as e:
            print(f"JSON 파싱 오류: {e}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"API 요청 실패: {e}")
        return None


def get_category_name(category_name: str) -> str:
    """
    ">"로 구분된 카테고리에서 2단계까지만 저장
    예) "국내도서>경제경영>재테크/투자" -> "국내도서 > 경제경영"
    """
    parts = category_name.split(">")
    if len(parts) >= 2:
        return " > ".join(parts[:2])
    return category_name


def _parse_pub_date(pub_date_str: str):
    """
    알라딘 pubDate 형식이 케이스에 따라 달라질 수 있어 여러 포맷 시도
    """
    if not pub_date_str:
        return None

    candidates = [
        "%a, %d %b %Y %H:%M:%S GMT",  # Mon, 01 Jan 2024 00:00:00 GMT
        "%Y-%m-%d",                   # 2024-01-01
        "%Y%m%d",                     # 20240101
    ]
    for fmt in candidates:
        try:
            return datetime.strptime(pub_date_str, fmt)
        except ValueError:
            continue

    print(f"날짜 파싱 실패: {pub_date_str}")
    return None


def save_books_to_db(books_data):
    if not books_data or "item" not in books_data:
        print("책 데이터를 가져오지 못했습니다.")
        return

    for item in books_data["item"]:
        try:
            title = item.get("title", "")
            author = item.get("author", "")
            publisher = item.get("publisher", "")
            pub_date_str = item.get("pubDate", None)
            isbn13 = item.get("isbn13", "")
            cover = _upgrade_cover_url(item.get("cover", "")) or ""
            description = item.get("description", "")
            customer_review_rank = item.get("customerReviewRank", None)

            if not isbn13:
                # isbn13 없는 데이터는 중복/식별이 어려워 스킵하는 게 안전
                print(f"[SKIP] isbn13 없음: {title}")
                continue

            # 카테고리 저장 (기존 카테고리가 없으면 새로 생성)
            category_name = item.get("categoryName", "기타")
            short_category_name = get_category_name(category_name)
            category, _ = Category.objects.get_or_create(name=short_category_name)

            pub_date = _parse_pub_date(pub_date_str)

            book, created = Book.objects.get_or_create(
                isbn13=isbn13,
                defaults={
                    "title": title,
                    "author": author,
                    "publisher": publisher,
                    "pub_date": pub_date,
                    "cover": cover,
                    "description": description,
                    "customer_review_rank": customer_review_rank,
                    "category": category,
                },
            )

            if created:
                print(f"[CREATED] {title}")
            else:
                print(f"[EXISTS]  {title}")

        except Exception as e:
            print(f"도서 '{item.get('title')}' 저장 중 오류 발생: {e}")


def fetch_and_save_books(total_pages=3, max_results=50, queries=None):
    query_list = queries if queries is not None else DEFAULT_QUERIES

    try:
        for query in query_list:
            print(f"\n========== [QUERY] {query} ==========")

            for page in range(total_pages):
                start_index = page + 1
                print(f"Fetching page {page + 1}/{total_pages} (Start index: {start_index})")

                books_data = get_books_from_aladin(
                    query=query,
                    max_results=max_results,
                    start_index=start_index,
                )

                items = (books_data or {}).get("item", [])
                if not items:
                    print(f"[STOP] '{query}' 더 이상 결과 없음 (page={page+1}) -> break")
                    break

                save_books_to_db(books_data)

        print(f"\nDONE. queries={len(query_list)}, pages_each={total_pages}")

    except Exception as e:
        print(f"도서 데이터를 저장하는데 실패했습니다: {e}")
        import traceback
        print("추가 오류 정보:")
        traceback.print_exc()
