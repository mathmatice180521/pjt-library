from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny

from .serializers import (
    RegisterSerializer,
    LogoutSerializer,
    MeSerializer,
    MeUpdateSerializer,
    DeleteMeSerializer,
)


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"message": "회원가입 성공", "user_id": user.id},
            status=status.HTTP_201_CREATED
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"message": "로그아웃 완료"}, status=status.HTTP_205_RESET_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data, status=status.HTTP_200_OK)

    def patch(self, request):
        serializer = MeUpdateSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(MeSerializer(request.user).data, status=status.HTTP_200_OK)


class DeleteMeView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        serializer = DeleteMeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        request.user.delete()
        return Response({"message": "회원탈퇴 완료"}, status=status.HTTP_200_OK)
