from django.db import transaction
from rest_framework import serializers
from .models import (
    Store,
    Sale, SaleItem, SaleTender,
    DeliveryOrderExtra,
    DeliveryOrderItem,
    DeliveryOrderItemOption, 
    DeliverySettlementDetail
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
    
    

class DeliverySettlementDetailSerializer(serializers.ModelSerializer):
    """정산 세부 항목 (773원 부가세 등 모든 비용)"""
    class Meta:
        model = DeliverySettlementDetail
        fields = ['date', 'category', 'item_name', 'amount', 'api_code']

class DeliveryOrderItemOptionSerializer(serializers.ModelSerializer):
    """배달 품목별 옵션 상세"""
    class Meta:
        model = DeliveryOrderItemOption
        fields = ['option_name', 'option_price', 'option_discount_price']

# [이름 변경] DeliveryIntegrationSerializer -> DeliverySaleSerializer
class DeliverySaleSerializer(serializers.Serializer):
    """
    배달 플랫폼 전용 데이터 직렬화.
    POS(Sale) 주문번호를 기준으로 배달 상세/정산 정보를 확장 저장합니다.
    """
    order_number = serializers.CharField(write_only=True)
    deposit_due_amount = serializers.IntegerField()
    deposit_due_date = serializers.DateField()
    pay_type = serializers.CharField()
    receive_type = serializers.CharField()
    
    items = serializers.JSONField(write_only=True) 
    settlements = DeliverySettlementDetailSerializer(many=True, write_only=True)

    def validate_order_number(self, value):
        """[검증] 연결할 POS 데이터(Sale)가 DB에 있는지 확인"""
        if not Sale.objects.filter(channel_order_no=value).exists():
            raise serializers.ValidationError(f"POS 주문번호 {value}가 존재하지 않습니다.")
        return value

    @transaction.atomic
    def create(self, validated_data):
        order_no = validated_data.pop('order_number')
        items_data = validated_data.pop('items')
        settlements_data = validated_data.pop('settlements')
        
        # 1. 대상 POS 주문(Sale) 획득
        sale = Sale.objects.get(channel_order_no=order_no)
        
        # 2. DeliveryOrderExtra: 입금 및 결제 정보 Upsert
        DeliveryOrderExtra.objects.update_or_create(
            sale=sale,
            defaults={
                'deposit_due_amount': validated_data.get('deposit_due_amount'),
                'deposit_due_date': validated_data.get('deposit_due_date'),
                'pay_type': validated_data.get('pay_type'),
                'receive_type': validated_data.get('receive_type'),
            }
        )

        # 3. DeliverySettlementDetail: 수수료 상세 내역 Upsert
        DeliverySettlementDetail.objects.filter(sale=sale).delete()
        DeliverySettlementDetail.objects.bulk_create([
            DeliverySettlementDetail(sale=sale, **s_data) 
            for s_data in settlements_data
        ])

        # 4. DeliveryOrderItem & Options: 배달 메뉴 및 옵션 Upsert
        for item_data in items_data:
            menu_name = item_data.get('menu_name')
            options_data = item_data.get('options', [])
            
            # POS 아이템과 매칭 시도
            sale_item = sale.items.filter(goods_nm=menu_name).first()
            
            delivery_item, _ = DeliveryOrderItem.objects.update_or_create(
                sale_item=sale_item,
                menu_name=menu_name,
                defaults={
                    'quantity': item_data.get('quantity', 1),
                    'price': item_data.get('price', 0),
                    'discount_price': item_data.get('discount_price', 0),
                }
            )

            # 옵션 재설정
            delivery_item.options.all().delete()
            if options_data:
                DeliveryOrderItemOption.objects.bulk_create([
                    DeliveryOrderItemOption(delivery_item=delivery_item, **opt) 
                    for opt in options_data
                ])

        return sale