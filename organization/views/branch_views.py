from rest_framework import generics, permissions
from organization.models.branch import Branch
from organization.serializers.branch_serializers import BranchSerializer, BranchCreateUpdateSerializer
from core.utils.db_utils import reset_id_sequence
from accounts.permissions import IsBranchOwnerOrManager

# Branch 목록 조회 및 생성
class BranchListCreateView(generics.ListCreateAPIView):
    queryset = Branch.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return BranchCreateUpdateSerializer
        return BranchSerializer

# Branch 상세 조회/수정/삭제
class BranchDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Branch.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsBranchOwnerOrManager]

    def get_serializer_class(self):
        if self.request.method in ["PUT", "PATCH"]:
            return BranchCreateUpdateSerializer
        return BranchSerializer

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        reset_id_sequence(Branch._meta.db_table)