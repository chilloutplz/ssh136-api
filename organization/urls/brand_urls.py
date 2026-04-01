from django.urls import path
from organization.views.brand_views import BrandListCreateView, BrandDetailView

urlpatterns = [
    path("", BrandListCreateView.as_view(), name="brand-list-create"),
    path("<int:pk>/", BrandDetailView.as_view(), name="brand-detail"),
]