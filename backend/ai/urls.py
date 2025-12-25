from django.urls import path
from .views import AIRecommendView, generate_comic_view

urlpatterns = [
    path("recommend/", AIRecommendView.as_view(), name="ai_recommend"),
    path("books/<int:book_id>/ai-content/", generate_comic_view, name="ai_content_generate"),
]
