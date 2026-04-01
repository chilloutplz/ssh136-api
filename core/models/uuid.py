# core/models/uuid.py
import uuid
from django.db import models

class UUIDModel(models.Model):
    """
    id를 Integer 대신 UUID로 사용하고 싶은 모델에서 상속.
    """
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )

    class Meta:
        abstract = True
