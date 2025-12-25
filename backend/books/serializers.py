from rest_framework import serializers
from .models import Book, Category
from interactions.models import Bookmark, Comment

class CategoryMiniSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ("id", "name")

class BookListSerializer(serializers.ModelSerializer):
    category = CategoryMiniSerializer(read_only=True)
    isbn = serializers.CharField(source="isbn13", allow_blank=True, required=False)
    cover_url = serializers.URLField(source="cover", allow_blank=True, required=False)

    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "author",
            "isbn",
            "cover_url",
            "category",
        )


class BookCommentSerializer(serializers.ModelSerializer):
    comment_id = serializers.IntegerField(source="id", read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = Comment
        fields = ("comment_id", "user_id", "username", "content", "created_at")


class BookDetailSerializer(serializers.ModelSerializer):
    isbn = serializers.CharField(source="isbn13", allow_blank=True, required=False)
    cover_url = serializers.URLField(source="cover", allow_blank=True, required=False)
    category = CategoryMiniSerializer(read_only=True)
    comment_count = serializers.IntegerField(read_only=True)
    is_bookmarked = serializers.SerializerMethodField()
    comments = BookCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Book
        fields = (
            "id",
            "title",
            "author",
            "publisher",
            "isbn",
            "description",
            "cover_url",
            "customer_review_rank",
            "is_bookmarked",
            "comment_count",
            "category",
            "comments",
        )

    def get_is_bookmarked(self, obj: Book) -> bool:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False

        return Bookmark.objects.filter(user=request.user, book=obj).exists()
