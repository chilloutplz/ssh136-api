from django.db import models
from core.models.base import BaseModel
from .company import Company

app_name = "brands"

class Brand(BaseModel):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="brands")
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.company.name} - {self.name}"