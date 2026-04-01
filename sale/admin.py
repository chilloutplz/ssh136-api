from django.contrib import admin
from .models import Store, Sale, SaleItem, SaleTender


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display  = ('code', 'name')
    search_fields = ('code', 'name')


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0
    fields = ('item_seq', 'goods_nm', 'goods_cd', 'sale_qty', 'app_prc', 'sale_amt', 'sale_except_yn')
    readonly_fields = fields


class SaleTenderInline(admin.TabularInline):
    model = SaleTender
    extra = 0
    fields = ('tender_seq', 'tender_nm', 'tender_cd', 'tender_amt', 'pre_tender_yn')
    readonly_fields = fields


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ('business_date', 'store', 'order_seq', 'channel', 'channel_detail', 'order_type', 'payment_status', 'actual_sale_amount', 'item_count')
    search_fields = ('channel_order_no', 'store__code', 'note')
    list_filter = ('business_date', 'store', 'channel', 'order_type', 'payment_status')
    ordering = ('-business_date', '-order_seq')
    inlines = [SaleItemInline, SaleTenderInline]

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = "상품수"


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    list_display = ('sale', 'item_seq', 'goods_nm', 'goods_cd', 'sale_qty', 'sale_amt', 'sale_except_yn')
    search_fields = ('goods_nm', 'goods_cd', 'sale__channel_order_no')
    list_filter = ('sale__business_date', 'sale_except_yn')
    ordering = ('-sale__business_date', 'item_seq')

    def subtotal(self, obj):
        return obj.subtotal
    subtotal.short_description = "소계"


@admin.register(SaleTender)
class SaleTenderAdmin(admin.ModelAdmin):
    list_display = ('sale', 'tender_seq', 'tender_nm', 'tender_cd', 'tender_amt', 'pre_tender_yn')
    search_fields = ('tender_cd', 'tender_nm', 'approval_no')
    list_filter = ('sale__business_date', 'tender_cd', 'pre_tender_yn')
    ordering = ('-sale__business_date', 'tender_seq')