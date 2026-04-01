from rest_framework import generics, permissions
from organization.models.brand import Brand
from organization.serializers.brand_serializers import BrandSerializer, BrandCreateUpdateSerializer
from core.utils.db_utils import reset_id_sequence
from accounts.permissions import IsBrandOwnerOrManager  # 필요시 권한 클래스 재사용

# 브랜드 목록 조회 및 생성
class BrandListCreateView(generics.ListCreateAPIView):
    queryset = Brand.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return BrandCreateUpdateSerializer
        return BrandSerializer


# 브랜드 상세 조회/수정/삭제
class BrandDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSerializer
    permission_classes = [permissions.IsAuthenticated, IsBrandOwnerOrManager]

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        # 브랜드 삭제 후 PK 시퀀스 재설정
        reset_id_sequence(Brand._meta.db_table)