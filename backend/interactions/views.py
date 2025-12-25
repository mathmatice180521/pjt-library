# backend/interactions/views.py
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from books.models import Book
from .models import Comment, Bookmark
from .serializers import (
    CommentCreateSerializer,
    CommentUpdateSerializer,
    MyCommentSerializer,
    MyBookmarkSerializer,
)


def _to_int(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


class BookCommentCreateView(APIView):
    """
    POST /api/v1/books/{book_id}/comments/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, book_id: int):
        book = get_object_or_404(Book, pk=book_id)

        serializer = CommentCreateSerializer(
            data=request.data,
            context={"request": request, "book": book},
        )
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()

        return Response(
            {"message": "댓글 작성 완료", "comment_id": comment.id},
            status=status.HTTP_200_OK,
        )


class CommentUpdateDeleteView(APIView):
    """
    PUT    /api/v1/comments/{comment_id}/
    DELETE /api/v1/comments/{comment_id}/
    """
    permission_classes = [IsAuthenticated]

    def _check_owner_or_admin(self, request, comment: Comment):
        # 작성자, 관리자만 사용 가능
        return (comment.user_id == request.user.id) or request.user.is_staff

    def put(self, request, comment_id: int):
        comment = get_object_or_404(Comment, pk=comment_id)

        if not self._check_owner_or_admin(request, comment):
            return Response({"message": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        serializer = CommentUpdateSerializer(comment, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({"message": "댓글 수정 완료"}, status=status.HTTP_200_OK)

    def delete(self, request, comment_id: int):
        comment = get_object_or_404(Comment, pk=comment_id)

        if not self._check_owner_or_admin(request, comment):
            return Response({"message": "권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        comment.delete()
        return Response({"message": "댓글 삭제 완료"}, status=status.HTTP_200_OK)


class MyCommentListView(APIView):
    """
    GET /api/v1/mypage/comments/?page=1&per_page=20
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = (
            Comment.objects
            .filter(user=request.user)
            .select_related("book")
            .order_by("-created_at")
        )

        page = max(_to_int(request.query_params.get("page"), 1), 1)
        per_page = min(max(_to_int(request.query_params.get("per_page"), 20), 1), 100)

        total_count = qs.count()
        total_pages = (total_count + per_page - 1) // per_page

        start = (page - 1) * per_page
        end = start + per_page
        page_qs = qs[start:end]

        data = MyCommentSerializer(page_qs, many=True).data
        return Response({
            "total_pages": total_pages,
            "page": page,
            "per_page": per_page,
            "results": data,
        }, status=status.HTTP_200_OK)



class BookBookmarkView(APIView):
    """
    POST   /api/v1/books/{book_id}/bookmark/
    DELETE /api/v1/books/{book_id}/bookmark/
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, book_id: int):
        book = get_object_or_404(Book, pk=book_id)
        Bookmark.objects.get_or_create(user=request.user, book=book)
        return Response({"message": "북마크 추가 완료"}, status=status.HTTP_200_OK)

    def delete(self, request, book_id: int):
        book = get_object_or_404(Book, pk=book_id)
        Bookmark.objects.filter(user=request.user, book=book).delete()
        return Response({"message": "북마크 삭제 완료"}, status=status.HTTP_200_OK)


class MyBookmarkListView(APIView):
    """
    GET /api/v1/mypage/bookmarks/?page=1&per_page=20
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = (
            Bookmark.objects
            .filter(user=request.user)
            .select_related("book")
            .order_by("-bookmarked_at")
        )

        page = max(_to_int(request.query_params.get("page"), 1), 1)
        per_page = min(max(_to_int(request.query_params.get("per_page"), 20), 1), 100)

        total_count = qs.count()
        total_pages = (total_count + per_page - 1) // per_page

        start = (page - 1) * per_page
        end = start + per_page
        page_qs = qs[start:end]

        data = MyBookmarkSerializer(page_qs, many=True).data
        return Response({
            "total_pages": total_pages,
            "page": page,
            "per_page": per_page,
            "results": data,
        }, status=status.HTTP_200_OK)

