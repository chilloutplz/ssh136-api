from django.urls import path
from accounts.views.auth_views import RegisterView, LoginView, RefreshTokenView, ApproveUserView

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("refresh/", RefreshTokenView.as_view(), name="token-refresh"),
    path("users/<int:pk>/approve/", ApproveUserView.as_view(), name="approve_user"),
]