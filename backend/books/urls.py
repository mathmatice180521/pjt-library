from django.urls import path
from .views import BookListView, BookDetailView

urlpatterns = [
    path("books/", BookListView.as_view(), name="book_list"),
    path("books/<int:book_id>/", BookDetailView.as_view(), name="book_detail"),
]
