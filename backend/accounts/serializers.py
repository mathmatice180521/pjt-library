from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("id", "username", "email", "password")

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("username exists")
        return value

    def validate_password(self, value):
        # Django 기본 비밀번호 검사
        validate_password(value)
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        refresh = attrs.get("refresh")
        try:
            self.token = RefreshToken(refresh)
        except Exception:
            raise serializers.ValidationError({"refresh": "잘못된 토큰"})
        return attrs

    def save(self, **kwargs):
        self.token.blacklist()


class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email")


class MeUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "email")

    extra_kwargs = {
        "username": {"required": False},
        "email": {"required": False},
    }

    def validate_username(self, value):
        # 내 username으로 다시 저장하는 건 OK, 다른 사람이 쓰는 건 막기
        user = self.instance  # request.user
        qs = User.objects.filter(username=value).exclude(pk=user.pk)
        if qs.exists():
            raise serializers.ValidationError("이미 사용 중인 username 입니다.")
        return value


class DeleteMeSerializer(serializers.Serializer):
    # 보안을 위해 보통 비밀번호 확인을 받음
    password = serializers.CharField(write_only=True, required=True)

    def validate(self, attrs):
        request = self.context["request"]
        password = attrs.get("password")

        # 비밀번호 확인을 강제하고 싶으면 required=True로 바꾸고 아래 주석 제거
        if password:
            if not request.user.check_password(password):
                raise serializers.ValidationError({"password": "비밀번호가 틀렸습니다."})
        return attrs
