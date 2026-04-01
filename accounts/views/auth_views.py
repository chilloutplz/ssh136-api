# accounts/views/auth_views.py
from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from accounts.serializers.auth_serializer import RegisterSerializer, LoginSerializer, ApproveUserSerializer
from accounts.models.user import User

# 관리자용 유저 승인 처리 뷰
class ApproveUserView(generics.UpdateAPIView):
    queryset = User.objects.all()
    serializer_class = ApproveUserSerializer
    permission_classes = [permissions.IsAdminUser]  # 관리자만 접근 가능


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer


class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer


class RefreshTokenView(TokenRefreshView):
    """
    JWT Refresh 토큰을 받아 Access 토큰을 재발급하는 뷰
    """
    # 필요하다면 serializer_class를 커스텀 가능
    # 기본은 rest_framework_simplejwt.serializers.TokenRefreshSerializer 사용
    pass

