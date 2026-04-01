from django.urls import path
from organization.views.company_views import (
    CompanyListCreateView,
    CompanyDetailView,
    CompanyMembersView
)

urlpatterns = [
    path("", CompanyListCreateView.as_view(), name="company-list-create"),
    path("<int:pk>/", CompanyDetailView.as_view(), name="company-detail"),
    path("<int:company_id>/members/", CompanyMembersView.as_view(), name="company-members"),
]
