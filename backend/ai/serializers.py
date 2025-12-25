from rest_framework import serializers
# [수정] AIContent 모델을 추가로 임포트해야 직접 조회가 가능합니다.
from .models import AIRecommendation, AIRecommendationItem, AIContent


# 1) 요청(Request)용
class AIRecommendRequestSerializer(serializers.Serializer):
    prompt = serializers.CharField(required=True, allow_blank=False, max_length=1000)

    mood = serializers.CharField(required=False, allow_blank=True, max_length=50)
    themes = serializers.ListField(
        child=serializers.CharField(max_length=30),
        required=False,
        allow_empty=True,
    )
    avoid = serializers.ListField(
        child=serializers.CharField(max_length=30),
        required=False,
        allow_empty=True,
    )

    pace = serializers.ChoiceField(
        choices=["slow", "medium", "fast"],
        required=False,
    )
    length = serializers.ChoiceField(
        choices=["short", "medium", "long"],
        required=False,
    )


# 2) 응답(Response)용
class AIRecommendationItemSerializer(serializers.ModelSerializer):
    book_pk = serializers.IntegerField(source="book.id", read_only=True)
    title = serializers.CharField(source="book.title", read_only=True)
    cover = serializers.CharField(source="book.cover", read_only=True)
    
    # [추가] 만화 이미지 URL을 가져오는 특수 필드
    comic_image_url = serializers.SerializerMethodField()

    class Meta:
        model = AIRecommendationItem
        # [추가] fields 목록에 comic_image_url 추가
        fields = ["book_pk", "title", "cover", "reason", "comic_image_url"]

    def get_comic_image_url(self, obj):
        """
        models.py를 수정하지 않고(related_name 없이),
        직접 AIContent 테이블에서 이 책(obj.book)에 해당하는 데이터를 찾습니다.
        """
        try:
            # AIContent 테이블에서 현재 책(obj.book)과 연결된 데이터를 찾음 (.first()로 안전하게 하나만 가져옴)
            content = AIContent.objects.filter(book=obj.book).first()
            
            # 데이터가 있고, 이미지 URL도 있다면 반환
            if content and content.comic_image_url:
                return content.comic_image_url
            return None
        except Exception:
            return None


class AIRecommendationSerializer(serializers.ModelSerializer):
    generated_at = serializers.DateTimeField(source="created_at", read_only=True)
    recommended_list = AIRecommendationItemSerializer(source="items", many=True, read_only=True)

    class Meta:
        model = AIRecommendation
        fields = ["recommended_list", "generated_at"]