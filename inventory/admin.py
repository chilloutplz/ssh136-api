from django.contrib import admin
from .models import Warehouse, Stock, StockTransaction

@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ("name", "location", "is_active")
    search_fields = ("name", "location")
    list_filter = ("is_active",)
    ordering = ("name",)

@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("product", "warehouse", "quantity")
    search_fields = ("product__name", "warehouse__name")
    list_filter = ("warehouse",)
    ordering = ("product__name",)

@admin.register(StockTransaction)
class StockTransactionAdmin(admin.ModelAdmin):
    list_display = ("transaction_type", "product", "warehouse", "quantity", "occurred_at")
    search_fields = ("product__name", "warehouse__name", "transaction_type")
    list_filter = ("transaction_type", "warehouse", "occurred_at")
    ordering = ("-occurred_at",)