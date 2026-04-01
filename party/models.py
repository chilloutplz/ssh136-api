from django.db import models
from core.models.base import BaseModel
from django.core.validators import RegexValidator as Reg

class Party(BaseModel):
    name = models.CharField(max_length=255)
    representative = models.CharField(max_length=255, blank=True, null=True)  # 대표자 이름
    business_number = models.CharField(
        max_length=10,
        blank=True,
        null=True,
        validators=[Reg(r'^\d{10}$', '사업자 등록번호는 10자리 숫자여야 합니다.')]
    )

    # 주소 관련 필드
    postcode = models.CharField(max_length=10, blank=True, null=True)        # 우편번호
    base_address = models.CharField(max_length=255, blank=True, null=True)   # 기본주소
    detail_address = models.CharField(max_length=255, blank=True, null=True) # 상세주소

    # 연락처 관련 필드
    phone = models.CharField(max_length=20, blank=True, null=True)           # 전화번호
    fax = models.CharField(max_length=20, blank=True, null=True)             # 팩스번호
    email = models.EmailField(blank=True, null=True)                         # 이메일

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name