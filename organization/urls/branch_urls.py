from django.urls import path
from organization.views.branch_views import BranchListCreateView, BranchDetailView

urlpatterns = [
    path("", BranchListCreateView.as_view(), name="branch-list-create"),
    path("<int:pk>/", BranchDetailView.as_view(), name="branch-detail"),
]