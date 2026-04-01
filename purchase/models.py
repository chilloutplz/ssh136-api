from django.db import models
from core.models.base import BaseModel
from party.models import Party
from product.models import Product

class Purchase(BaseModel):
    supplier = models.ForeignKey(
        Party,
        on_delete=models.PROTECT,
        related_name="purchases"
    )
    purchased_at = models.DateTimeField()
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    note = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-purchased_at"]

    def __str__(self):
        return f"Purchase {self.id} from {self.supplier.name}"

class PurchaseItem(BaseModel):
    purchase = models.ForeignKey(
        Purchase,
        on_delete=models.CASCADE,
        related_name="items"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT
    )
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"