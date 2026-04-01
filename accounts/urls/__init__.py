# accounts/urls/__init__.py
from django.urls import include, path

urlpatterns = [
    path("users/", include("accounts.urls.user_urls")),
    path("auth/", include("accounts.urls.auth_urls")),
]