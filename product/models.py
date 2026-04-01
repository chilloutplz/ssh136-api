# product/models.py
from django.db import models
from core.models.base import BaseModel   #  BaseModel 사용

class Product(BaseModel):   #  BaseModel 상속
    code = models.CharField(max_length=64, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)

    # 기본 단위 (재고/BOM 기준)
    base_unit = models.CharField(max_length=32, default="EA")

    # 구매 단위 (발주 기준)
    purchase_unit = models.CharField(max_length=32, default="EA")
    purchase_conversion_factor = models.DecimalField(
        max_digits=12, decimal_places=3, default=1,
        help_text="1 purchase_unit = N base_unit"
    )

    # 판매 단위 (판매 기준)
    sales_unit = models.CharField(max_length=32, default="EA")
    sales_conversion_factor = models.DecimalField(
        max_digits=12, decimal_places=3, default=1,
        help_text="1 sales_unit = N base_unit"
    )

    spec = models.CharField(max_length=255, blank=True)
    is_resell = models.BooleanField(default=False)
    is_stock_managed = models.BooleanField(default=False)   # 재고관리 여부 - default: False

    vat_rate = models.DecimalField(
        max_digits=4, decimal_places=2, default=0.1,
        help_text="부가세율 (예: 0.1 = 10%, 0 = 면세)"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["code"],
                condition=models.Q(code__isnull=False),
                name="unique_product_code_not_null",
            )
        ]

    def __str__(self):
        return f"{self.code or '-'} | {self.name}"


class ProductAlias(models.Model):
    """
    플랫폼별 상품명 → 내부 Product 매핑
    """

    name = models.CharField(max_length=200, unique=True)

    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="aliases"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    
    
class BOM(BaseModel):   #  BaseModel 상속
    parent = models.ForeignKey(Product, related_name="bom_parents", on_delete=models.CASCADE)
    component = models.ForeignKey(Product, related_name="bom_components", on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)

    class Meta:
        unique_together = ("parent", "component")
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(parent=models.F("component")),
                name="bom_no_self_reference"
            ),
            models.CheckConstraint(
                condition=models.Q(quantity__gt=0),
                name="bom_quantity_positive"
            ),
        ]