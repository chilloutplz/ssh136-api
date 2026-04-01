# core/models/base.py
from django.db import models

class BaseModel(models.Model):
    """
    프로젝트 내 모든 모델이 상속받는 기본 베이스 모델.
    created_at / updated_at / is_active 포함.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True