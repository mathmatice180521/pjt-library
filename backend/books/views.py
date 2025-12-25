from django.db.models import Q, Count, Prefetch
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import Book
from .serializers import BookListSerializer, BookDetailSerializer
from interactions.models import Comment

def _to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class BookListView(APIView):
    """
    GET /api/v1/books/
    Query: ?q=검색어&category=카테고리ID&page=1&per_page=20&sort=latest
    """

    def get(self, request):
        qs = Book.objects.all()

        # paging (명세서: page, per_page) — 먼저 파싱해서 빈 결과에도 동일 포맷 응답
        page = max(_to_int(request.query_params.get("page"), 1), 1)
        per_page = _to_int(request.query_params.get("per_page"), 20)
        per_page = min(max(per_page, 1), 100)

        # q 검색
        q = request.query_params.get("q")
        field = (request.query_params.get("field") or "all").lower()

        if q:
            if field == "title":
                qs = qs.filter(title__icontains=q)
            elif field == "author":
                qs = qs.filter(author__icontains=q)
            elif field == "publisher":
                qs = qs.filter(publisher__icontains=q)
            else:  # all
                qs = qs.filter(
                    Q(title__icontains=q) |
                    Q(author__icontains=q) |
                    Q(publisher__icontains=q)
                )

        # category 필터 (명세서: category=카테고리ID)
        category_id = _to_int(request.query_params.get("category"), None)
        if category_id:
            qs = qs.filter(category_id=category_id)

        # sort (명세서: latest, oldest)
        sort = (request.query_params.get("sort") or "latest").lower()
        if sort == "latest":
            qs = qs.order_by("-pub_date")
        elif sort == "oldest":
            qs = qs.order_by("pub_date")
        else:
            qs = qs.order_by("-pub_date")

        # total_pages 계산 (응답엔 total_count 안 넣음)
        total_count = qs.count()
        total_pages = (total_count + per_page - 1) // per_page

        start = (page - 1) * per_page
        end = start + per_page
        page_qs = qs[start:end]

        data = BookListSerializer(page_qs, many=True).data

        payload = {
            "total_pages": total_pages,
            "page": page,
            "per_page": per_page,
            "results": data,
        }
        if q and total_count == 0:
            payload["message"] = "검색 결과가 없습니다."

        return Response(payload, status=status.HTTP_200_OK)


class BookDetailView(APIView):
    """
    GET /api/v1/books/{book_id}/
    """

    def get(self, request, book_id: int):
        book = (
            Book.objects
            .select_related("category")
            .annotate(comment_count=Count("comments", distinct=True))
            .prefetch_related(
                Prefetch(
                    "comments",
                    queryset=Comment.objects.select_related("user").order_by("-created_at")
                )
            )
            .filter(pk=book_id)
            .first()
        )
        if not book:
            return Response({"message": "도서를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        data = BookDetailSerializer(book, context={"request": request}).data
        return Response(data, status=status.HTTP_200_OK)
