from django.db import models
from core.models.base import BaseModel
from .brand import Brand

class Branch(BaseModel):
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, related_name="branches")
    name = models.CharField(max_length=100)                # 지점명
    representative = models.CharField(max_length=100, blank=True, null=True)      # 대표자
    postcode = models.CharField(max_length=20, blank=True, null=True)          # 우편번호
    base_address = models.CharField(max_length=255, blank=True, null=True)             # 주소
    detail_address = models.CharField(max_length=255, blank=True, null=True)  # 세부주소
    phone = models.CharField(max_length=50, blank=True, null=True)            # 전화번호
    email = models.EmailField(blank=True, null=True)       # 이메일
    description = models.TextField(blank=True, null=True)  # 설명

    def __str__(self):
        return f"{self.brand.name} - {self.name}"