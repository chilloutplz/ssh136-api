# accounts/urls/__init__.py
from django.urls import include, path

urlpatterns = [
    path("companies/", include("organization.urls.company_urls")),
    path("brands/", include("organization.urls.brand_urls")),
    path("branches/", include("organization.urls.branch_urls")),
]