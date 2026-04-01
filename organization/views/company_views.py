from core.utils.db_utils import reset_id_sequence

from rest_framework import generics, permissions
from rest_framework.permissions import BasePermission
from organization.models.company import Company, UserCompanyRole
from organization.serializers.company_serializers import (
    CompanySerializer,
    CompanyCreateUpdateSerializer,
    CompanyMembershipSerializer,
)

#  커스텀 권한 클래스
class IsCompanyOwnerOrManager(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # obj가 Brand 같은 다른 모델일 경우 company 필드에서 Company 추출
        company = getattr(obj, "company", obj)
        role = UserCompanyRole.objects.filter(user=request.user, company=company).first()
        return role and role.role in ["owner", "manager"]


#  회사 목록 조회 및 생성
class CompanyListCreateView(generics.ListCreateAPIView):
    queryset = Company.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return CompanyCreateUpdateSerializer
        return CompanySerializer

    def perform_create(self, serializer):
        # 회사 생성 시 현재 유저를 자동으로 owner로 등록
        company = serializer.save()
        UserCompanyRole.objects.create(
            user=self.request.user,
            company=company,
            role="owner"
        )


#  회사 상세 조회/수정/삭제
class CompanyDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Company.objects.all()
    serializer_class = CompanySerializer
    permission_classes = [permissions.IsAuthenticated, IsCompanyOwnerOrManager]
    
    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        # 회사 삭제 후 PK 시퀀스 재설정
        reset_id_sequence(Company._meta.db_table)


#  특정 회사 멤버 조회
class CompanyMembersView(generics.ListAPIView):
    serializer_class = CompanyMembershipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        company_id = self.kwargs["company_id"]
        # select_related로 user까지 한 번에 가져와 N+1 문제 방지
        return UserCompanyRole.objects.filter(company_id=company_id).select_related("user")