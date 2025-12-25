from django.db import models
from django.conf import settings

from books.models import Book


class AIContent(models.Model):
    """(기존 유지) 책 1권에 대한 AI 생성 컨텐츠(요약/만화 등)"""

    book = models.OneToOneField(Book, on_delete=models.CASCADE, related_name="ai_content")
    summary_text = models.TextField(blank=True)
    comic_image_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class BookEmbedding(models.Model):
    """책 1권당 1개 임베딩(의미 벡터) 저장용 테이블.

    - AIContent를 나중에 다른 용도로 쓰고 싶을 때, 임베딩을 분리 보관하기 위해 추가
    - 추천 파이프라인(semantic search)에서 사용
    """

    book = models.OneToOneField(Book, on_delete=models.CASCADE, related_name="ai_embedding")
    embedding = models.JSONField(null=True, blank=True)  # list[float]
    embedding_norm = models.FloatField(null=True, blank=True)  # cosine 계산 최적화
    embedding_model = models.CharField(max_length=64, default="gemini-embedding-001")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"BookEmbedding(book_id={self.book_id})"


class AIRecommendation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class AIRecommendationItem(models.Model):
    recommendation = models.ForeignKey(AIRecommendation, on_delete=models.CASCADE, related_name="items")
    book = models.ForeignKey("books.Book", on_delete=models.PROTECT)  # 이력 보존이면 PROTECT 추천
    reason = models.TextField()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["recommendation", "book"], name="uniq_reco_book"),
        ]
