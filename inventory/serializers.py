from rest_framework import serializers
from .models import Warehouse, Stock, StockTransaction
from product.models import Product

class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = "__all__"

class StockSerializer(serializers.ModelSerializer):
    product = serializers.StringRelatedField(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product", write_only=True
    )
    warehouse = serializers.StringRelatedField(read_only=True)
    warehouse_id = serializers.PrimaryKeyRelatedField(
        queryset=Warehouse.objects.all(), source="warehouse", write_only=True
    )

    class Meta:
        model = Stock
        fields = ["id", "product", "product_id", "warehouse", "warehouse_id", "quantity"]

class StockTransactionSerializer(serializers.ModelSerializer):
    product = serializers.StringRelatedField(read_only=True)
    product_id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(), source="product", write_only=True
    )
    warehouse = serializers.StringRelatedField(read_only=True)
    warehouse_id = serializers.PrimaryKeyRelatedField(
        queryset=Warehouse.objects.all(), source="warehouse", write_only=True
    )

    class Meta:
        model = StockTransaction
        fields = [
            "id", "product", "product_id", "warehouse", "warehouse_id",
            "transaction_type", "quantity", "note", "occurred_at"
        ]