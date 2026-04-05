from django.db import transaction
from rest_framework import serializers
from sale.models import (
    Store,
    Sale, SaleItem, SaleTender,
)

class SaleItemSerializer(serializers.Serializer):
    """
    MATE POS 상세 API items[] 단일 항목.
    배달비(DLV00), 채널할인(DSC00) 같은 가상 항목 포함.
    sale_except_yn='Y' 인 항목은 매출 집계에서 제외.
    """

    item_seq           = serializers.IntegerField()
    goods_cd           = serializers.CharField()
    goods_nm           = serializers.CharField()
    app_prc            = serializers.IntegerField(default=0)
    sale_qty           = serializers.IntegerField(default=0)
    sale_amt           = serializers.IntegerField(default=0)
    item_dc_amt        = serializers.IntegerField(default=0)
    taxable_amount     = serializers.IntegerField(default=0)
    vat                = serializers.IntegerField(default=0)
    non_taxable_amount = serializers.IntegerField(default=0)
    sale_except_amt    = serializers.IntegerField(default=0)
    sale_except_yn     = serializers.CharField(default='N')
    packing_yn         = serializers.CharField(default='N')
    # 옵션/세트 중첩 구조는 JSON 그대로 보관
    item_details       = serializers.ListField(default=list)
    item_opt_details   = serializers.ListField(default=list)


class SaleTenderSerializer(serializers.Serializer):
    """
    MATE POS 상세 API tenders[] 단일 결제수단.
    복합결제 시 여러 행 존재.
    예) 선결제(PREPAID) + 채널할인즉시(IMMEDDSC) + 배달앱할인(CHANNELDSC)
    """

    tender_seq    = serializers.IntegerField()
    # tenderCd 원본값 유지 (PREPAID / CARD / CASH / IMMEDDSC / CHANNELDSC 등)
    tender_cd     = serializers.CharField()
    tender_nm     = serializers.CharField()
    tender_amt    = serializers.IntegerField(default=0)
    change_amt    = serializers.IntegerField(default=0)
    pre_tender_yn = serializers.CharField(default='N')
    return_yn     = serializers.CharField(default='N')
    # 현장 카드결제 시에만 값 존재
    approval_no   = serializers.CharField(allow_null=True, required=False)
    approval_dt   = serializers.CharField(allow_null=True, required=False)
    pur_nm        = serializers.CharField(allow_null=True, required=False)


class SaleSerializer(serializers.Serializer):
    """
    주문 단건 직렬화.
    ModelSerializer 대신 Serializer 사용 — 중첩 items/tenders 를
    직접 제어하기 위함.
    create() 에서 update_or_create 처리 → 재전송 시 안전하게 덮어씀.
    """

    # ── 매장 ─────────────────────────────────────────────────
    # store_code/store_name → Store get_or_create → FK 연결
    store_code = serializers.CharField()
    store_name = serializers.CharField()

    # ── 날짜/시간 ─────────────────────────────────────────────
    business_date = serializers.DateField()
    sold_at       = serializers.DateTimeField(allow_null=True, required=False)

    # ── 주문 식별 ─────────────────────────────────────────────
    order_seq        = serializers.IntegerField()
    # 배달 플랫폼 주문번호 (배민: T2BK0001TC0J 형태)
    channel_order_no = serializers.CharField(allow_null=True, required=False)

    # ── 주문 분류 ─────────────────────────────────────────────
    order_category = serializers.CharField()
    channel        = serializers.CharField()
    channel_detail = serializers.CharField(default='', allow_blank=True)  # POS 원본값 그대로
    order_type     = serializers.CharField()

    # ── 결제 ─────────────────────────────────────────────────
    payment_status   = serializers.CharField()
    payment_method   = serializers.CharField(default='', allow_blank=True)
    delivery_company = serializers.CharField(allow_null=True, required=False)

    # ── 금액 (원화 정수) ─────────────────────────────────────
    sale_amount          = serializers.IntegerField(default=0)
    discount_amount      = serializers.IntegerField(default=0)
    net_sale_amount      = serializers.IntegerField(default=0)
    channel_delivery_fee = serializers.IntegerField(default=0)
    channel_discount     = serializers.IntegerField(default=0)
    actual_sale_amount   = serializers.IntegerField(default=0)  # 핵심 매출 기준값
    taxable_amount       = serializers.IntegerField(default=0)
    vat                  = serializers.IntegerField(default=0)
    non_taxable_amount   = serializers.IntegerField(default=0)
    cup_deposit          = serializers.IntegerField(default=0)
    online_delivery_fee  = serializers.IntegerField(default=0)

    # ── 기타 ─────────────────────────────────────────────────
    mate_qr_order_no  = serializers.CharField(allow_null=True, required=False)
    note              = serializers.CharField(allow_null=True, required=False)
    # ── 반품 원본 주문 참조 ───────────────────────────────────
    org_business_date = serializers.DateField(allow_null=True, required=False)
    org_order_seq     = serializers.CharField(allow_null=True, required=False)
    raw_data         = serializers.JSONField(required=False)

    # ── 중첩 데이터 ───────────────────────────────────────────
    items   = SaleItemSerializer(many=True, required=False, default=list)
    tenders = SaleTenderSerializer(many=True, required=False, default=list)

    def create(self, validated_data):
        items_data   = validated_data.pop("items", [])
        tenders_data = validated_data.pop("tenders", [])

        # Store get_or_create
        store_code = validated_data.pop("store_code")
        store_name = validated_data.pop("store_name")
        store, _ = Store.objects.get_or_create(
            code=store_code,
            defaults={"name": store_name},
        )

        # unique_together(store, business_date, order_seq) 기준 upsert
        sale, _ = Sale.objects.update_or_create(
            store=store,
            business_date=validated_data["business_date"],
            order_seq=validated_data["order_seq"],
            defaults={**validated_data, "source": "matepos"},
        )

        # items / tenders 는 항상 최신 상태로 재생성
        sale.items.all().delete()
        SaleItem.objects.bulk_create([
            SaleItem(sale=sale, **item) for item in items_data
        ])

        sale.tenders.all().delete()
        SaleTender.objects.bulk_create([
            SaleTender(sale=sale, **tender) for tender in tenders_data
        ])

        return sale
    
    
