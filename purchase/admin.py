from django.contrib import admin
from .models import Purchase, PurchaseItem

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ('purchased_at', 'supplier', 'item_count', 'total_price')
    search_fields = ('supplier__name',)   # supplier는 Party FK
    list_filter = ('purchased_at',)
    ordering = ('-purchased_at',)

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = "Items"

@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'unit_price', 'total_price')
    search_fields = ('product__name', 'purchase__id')
    list_filter = ('purchase__purchased_at',)
    ordering = ('-purchase__purchased_at',)

    def total_price(self, obj):
        return obj.quantity * obj.unit_price
    total_price.short_description = "Total Price"