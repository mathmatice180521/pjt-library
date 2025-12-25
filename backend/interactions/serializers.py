from rest_framework import serializers
from .models import Comment, Bookmark


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("content",)

    def create(self, validated_data):
        request = self.context["request"]
        book = self.context["book"]
        return Comment.objects.create(user=request.user, book=book, **validated_data)


class CommentUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("content",)


class MyCommentSerializer(serializers.ModelSerializer):
    comment_id = serializers.IntegerField(source="id", read_only=True)
    book_id = serializers.IntegerField(source="book.id", read_only=True)
    book_title = serializers.CharField(source="book.title", read_only=True)

    class Meta:
        model = Comment
        fields = ("comment_id", "book_id", "book_title", "content", "created_at")


class MyBookmarkSerializer(serializers.ModelSerializer):
    book_id = serializers.IntegerField(source="book.id", read_only=True)
    title = serializers.CharField(source="book.title", read_only=True)
    author = serializers.CharField(source="book.author", read_only=True)
    cover_url = serializers.URLField(source="book.cover", allow_blank=True, required=False)

    class Meta:
        model = Bookmark
        fields = ("book_id", "title", "author", "cover_url")
