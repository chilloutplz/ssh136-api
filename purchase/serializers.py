from rest_framework import serializers
from decimal import Decimal
from .models import Purchase, PurchaseItem
from party.models import Party
from product.models import Product
from inventory.models import Stock, StockTransaction, Warehouse
from accounting.utils import upsert_purchase_entry, delete_purchase_entry


class PurchaseItemSerializer(serializers.ModelSerializer):
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        source="product",
        write_only=True
    )
    product = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = PurchaseItem
        fields = ["id", "product", "product_id", "quantity", "unit_price"]

class PurchaseSerializer(serializers.ModelSerializer):
    items = serializers.ListField(write_only=True)

    class Meta:
        model = Purchase
        fields = ["id", "party", "purchased_at", "total_price", "items"]

    def _recalc_total(self, purchase) -> Decimal:
        return sum(Decimal(pi.quantity) * Decimal(pi.unit_price) for pi in purchase.items.all())

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        purchase = Purchase.objects.create(**validated_data)
        warehouse = Warehouse.objects.first()
        total = Decimal("0")

        for item in items_data:
            pi = PurchaseItem.objects.create(purchase=purchase, **item)
            total += Decimal(pi.quantity) * Decimal(pi.unit_price)

            if pi.product.is_stock_managed:
                stock, _ = Stock.objects.get_or_create(product=pi.product, warehouse=warehouse)
                stock.quantity += pi.quantity
                stock.save()

                StockTransaction.objects.create(
                    product=pi.product,
                    warehouse=warehouse,
                    transaction_type=StockTransaction.INBOUND,
                    quantity=pi.quantity,
                    note=f"Purchase {purchase.id}",
                    occurred_at=purchase.purchased_at,
                )

        purchase.total_price = total
        purchase.save(update_fields=["total_price"])

        # Accounting 반영 (Create)
        upsert_purchase_entry(purchase, total)
        return purchase

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items", [])
        warehouse = Warehouse.objects.first()

        # 기존 아이템 업데이트
        for item_data in items_data:
            pi = PurchaseItem.objects.get(id=item_data["id"])
            old_qty = pi.quantity
            new_qty = item_data.get("quantity", old_qty)
            diff = new_qty - old_qty

            if pi.product.is_stock_managed and diff != 0:
                stock = Stock.objects.get(product=pi.product, warehouse=warehouse)
                stock.quantity += diff
                stock.save()

                txn = StockTransaction.objects.filter(
                    product=pi.product,
                    warehouse=warehouse,
                    note__contains=f"Purchase {instance.id}"
                ).first()
                if txn:
                    txn.quantity += diff
                    txn.save()

            for attr, value in item_data.items():
                setattr(pi, attr, value)
            pi.save()

        # 헤더 업데이트
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 총액 재계산
        total = self._recalc_total(instance)
        instance.total_price = total
        instance.save(update_fields=["total_price"])

        # Accounting 반영 (Update)
        upsert_purchase_entry(instance, total)
        return instance

    def perform_destroy(self, instance):
        warehouse = Warehouse.objects.first()
        for pi in instance.items.all():
            if pi.product.is_stock_managed:
                stock = Stock.objects.get(product=pi.product, warehouse=warehouse)
                stock.quantity -= pi.quantity
                stock.save()

                StockTransaction.objects.filter(
                    product=pi.product,
                    warehouse=warehouse,
                    note__contains=f"Purchase {instance.id}"
                ).delete()

        # Accounting 반영 (Delete)
        delete_purchase_entry(instance.id)

        instance.items.all().delete()
        instance.delete()

