from django.urls import path
from accounts.views.user_views import UserMeView, UserListView, UserUpdateView

urlpatterns = [
    path("me/", UserMeView.as_view(), name="user-me"),              # 내 정보 조회
    path("me/update/", UserUpdateView.as_view(), name="user-update"), # 내 정보 수정
    path("", UserListView.as_view(), name="user-list"),             # 전체 유저 조회 (관리자용)
]
