from rest_framework.permissions import BasePermission
from organization.models.company import UserCompanyRole
from organization.models.brand import Brand
from organization.models.branch import Branch

# 회사 권한: owner 또는 manager만 수정/삭제 가능
class IsCompanyOwnerOrManager(BasePermission):
    def has_object_permission(self, request, view, obj):
        role = UserCompanyRole.objects.filter(user=request.user, company=obj).first()
        return role and role.role in ["owner", "manager"]


# 브랜드 권한: 해당 브랜드가 속한 회사에서 owner/manager 권한을 가진 경우만 수정/삭제 가능
class IsBrandOwnerOrManager(BasePermission):
    def has_object_permission(self, request, view, obj: Brand):
        role = UserCompanyRole.objects.filter(user=request.user, company=obj.company).first()
        return role and role.role in ["owner", "manager"]


# 지점 권한: 해당 지점이 속한 브랜드 → 회사에서 owner/manager 권한을 가진 경우만 수정/삭제 가능
class IsBranchOwnerOrManager(BasePermission):
    def has_object_permission(self, request, view, obj):
        # obj가 Branch일 경우 brand → company 추출
        company = getattr(obj.brand, "company", None)
        role = UserCompanyRole.objects.filter(user=request.user, company=company).first()
        return role and role.role in ["owner", "manager"]
