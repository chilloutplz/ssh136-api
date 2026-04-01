from django.contrib import admin
from .models import User
from organization.models.company import Company, UserCompanyRole
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    # 기본 UserAdmin의 fieldsets를 커스텀 모델에 맞게 수정
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Personal info"), {"fields": ("name", "phone")}),
        (_("Permissions"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
        (_("Status"), {"fields": ("status",)}),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": ("email", "name", "phone", "password1", "password2", "status"),
        }),
    )

    list_display = ("email", "name", "phone", "status", "is_staff")
    search_fields = ("email", "name", "phone")
    ordering = ("email",)


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("name", "business_number", "representative")
    search_fields = ("name", "business_number")

@admin.register(UserCompanyRole)
class UserCompanyRoleAdmin(admin.ModelAdmin):
    list_display = ("user", "company", "role")
    list_filter = ("role",)
