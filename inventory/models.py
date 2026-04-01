from django.db import models
from core.models.base import BaseModel
from product.models import Product

class Warehouse(BaseModel):
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name

class Stock(BaseModel):
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stocks")
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT, related_name="stocks")
    quantity = models.DecimalField(max_digits=12, decimal_places=3, default=0)

    class Meta:
        unique_together = ("product", "warehouse")

    def __str__(self):
        return f"{self.product.name} @ {self.warehouse.name} ({self.quantity})"

class StockTransaction(BaseModel):
    INBOUND = "IN"
    OUTBOUND = "OUT"
    ADJUST = "ADJ"
    MOVE = "MOVE"

    TRANSACTION_TYPES = [
        (INBOUND, "Inbound"),
        (OUTBOUND, "Outbound"),
        (ADJUST, "Adjustment"),
        (MOVE, "Move"),
    ]

    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.PROTECT)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPES)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    note = models.TextField(blank=True, null=True)
    occurred_at = models.DateTimeField()

    def __str__(self):
        return f"{self.transaction_type} {self.product.name} {self.quantity}"