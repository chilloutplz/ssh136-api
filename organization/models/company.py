from django.core.validators import RegexValidator as Reg
from django.db import models
from core.models import BaseModel
from accounts.models import User


class Company(BaseModel):
    name = models.CharField(max_length=255)
    representative = models.CharField(max_length=255, blank=True, null=True)  # 대표자 이름
    business_number = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[Reg(r'^\d{10}$', '사업자 등록번호는 10자리 숫자여야 합니다.')]
    )

    # 주소 관련 필드 분리
    postcode = models.CharField(max_length=10, blank=True, null=True)          # 우편번호
    base_address = models.CharField(max_length=255, blank=True, null=True)     # 기본주소
    detail_address = models.CharField(max_length=255, blank=True, null=True)   # 상세주소

    # 연락처 관련 필드
    phone = models.CharField(max_length=20, blank=True, null=True)             # 전화번호
    fax = models.CharField(max_length=20, blank=True, null=True)               # 팩스번호
    email = models.EmailField(blank=True, null=True)                           # 이메일

    def __str__(self):
        return self.name


class UserCompanyRole(BaseModel):
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
        ('accountant', 'Accountant'),
    ]

    user = models.ForeignKey(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="company_roles"
    )
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        related_name="members"
    )
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default="staff")

    class Meta:
        unique_together = ('user', 'company')

    def __str__(self):
        return f"{self.user.email} @ {self.company.name} ({self.role})"