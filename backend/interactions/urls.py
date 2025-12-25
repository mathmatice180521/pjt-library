from django.urls import path
from .views import (
    BookCommentCreateView,
    CommentUpdateDeleteView,
    MyCommentListView,
    BookBookmarkView,
    MyBookmarkListView,
)

urlpatterns = [
    # comment
    path("books/<int:book_id>/comments/", BookCommentCreateView.as_view()),
    path("comments/<int:comment_id>/", CommentUpdateDeleteView.as_view()),
    path("mypage/comments/", MyCommentListView.as_view()),

    # bookmark
    path("books/<int:book_id>/bookmark/", BookBookmarkView.as_view()),
    path("mypage/bookmarks/", MyBookmarkListView.as_view()),
]
