# core/models/mixins.py
from django.db import models
from django.utils import timezone

class SoftDeleteMixin(models.Model):
    """
    실제 삭제 대신 is_deleted 플래그만 변경하는 소프트 삭제 기능.
    """
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)

    def delete(self, using=None, keep_parents=False):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    class Meta:
        abstract = True


class TimeStampMixin(models.Model):
    """
    생성/수정 시간만 필요한 경우 사용하는 타임스탬프 믹스인.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
