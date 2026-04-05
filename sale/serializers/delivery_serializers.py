from rest_framework import serializers
from sale.models import (
    Sale,
    DeliveryOrder,
    DeliveryOrderItem,
    DeliveryOrderItemOption,
    DeliverySettlementDetail,
    DeliveryBaeminInfo,
)


class DeliveryOrderItemOptionSerializer(serializers.Serializer):
    name  = serializers.CharField(allow_blank=True, default='')
    price = serializers.IntegerField(default=0)


class DeliveryOrderItemSerializer(serializers.Serializer):
    item_seq      = serializers.IntegerField()
    name          = serializers.CharField()
    quantity      = serializers.IntegerField(default=1)
    total_price   = serializers.IntegerField(default=0)
    discount_price = serializers.IntegerField(default=0)
    options       = DeliveryOrderItemOptionSerializer(many=True, default=list)


class DeliverySettlementDetailSerializer(serializers.Serializer):
    group  = serializers.ChoiceField(choices=['ORDER', 'DELIVERY', 'ETC'])
    code   = serializers.CharField()
    name   = serializers.CharField()
    amount = serializers.IntegerField(default=0)


class DeliveryBaeminInfoSerializer(serializers.Serializer):
    ad_campaign_key        = serializers.CharField(allow_blank=True, default='')
    is_club_member         = serializers.BooleanField(default=False)
    delivery_carry_type    = serializers.CharField(allow_blank=True, default='')
    shop_discount          = serializers.IntegerField(default=0)
    order_instant_discount = serializers.IntegerField(default=0)
    total_instant_discount = serializers.IntegerField(default=0)
    order_brokerage_amount = serializers.IntegerField(default=0)
    delivery_item_amount   = serializers.IntegerField(default=0)
    etc_item_amount        = serializers.IntegerField(default=0)
    deduction_vat          = serializers.IntegerField(default=0)


class DeliveryOrderSerializer(serializers.Serializer):
    """
    배달 플랫폼 주문 단건 직렬화.
    create() 에서:
      1. channel_order_no 로 Sale 자동 매칭
      2. DeliveryOrder update_or_create
      3. items / settlement_details / platform_info 재생성
    """

    # ── 플랫폼 ───────────────────────────────────────────────
    platform     = serializers.ChoiceField(choices=['BAEMIN', 'COUPANG', 'YOGIYO'])
    order_number = serializers.CharField()

    # ── 주문 기본 ────────────────────────────────────────────
    order_datetime = serializers.DateTimeField()
    status         = serializers.CharField()
    delivery_type  = serializers.CharField(allow_blank=True, default='')
    pay_type       = serializers.CharField(allow_blank=True, default='')
    pay_amount     = serializers.IntegerField(default=0)
    items_summary  = serializers.CharField(allow_blank=True, default='')

    # ── 정산 ─────────────────────────────────────────────────
    deposit_due_amount = serializers.IntegerField(default=0)
    deposit_due_date   = serializers.DateField(allow_null=True, required=False)

    # ── 중첩 데이터 ───────────────────────────────────────────
    items               = DeliveryOrderItemSerializer(many=True, default=list)
    settlement_details  = DeliverySettlementDetailSerializer(many=True, default=list)

    # ── 플랫폼별 부가정보 (플랫폼에 따라 하나만 존재) ──────────
    baemin_info = DeliveryBaeminInfoSerializer(required=False, allow_null=True)

    # ── 원본 ─────────────────────────────────────────────────
    raw_data = serializers.JSONField(required=False)

    def create(self, validated_data):
        items_data      = validated_data.pop("items", [])
        settle_data     = validated_data.pop("settlement_details", [])
        baemin_info_data = validated_data.pop("baemin_info", None)

        # ── Sale 자동 매칭 ─────────────────────────────────────
        order_number = validated_data["order_number"]
        sale = Sale.objects.filter(channel_order_no=order_number).first()

        # ── DeliveryOrder upsert ──────────────────────────────
        delivery_order, _ = DeliveryOrder.objects.update_or_create(
            order_number=order_number,
            defaults={**validated_data, "sale": sale},
        )

        # ── items 재생성 ──────────────────────────────────────
        delivery_order.items.all().delete()
        for item_data in items_data:
            options_data = item_data.pop("options", [])
            item = DeliveryOrderItem.objects.create(
                order=delivery_order,
                **item_data,
            )
            DeliveryOrderItemOption.objects.bulk_create([
                DeliveryOrderItemOption(item=item, **opt)
                for opt in options_data
            ])

        # ── settlement_details 재생성 ─────────────────────────
        delivery_order.settlement_details.all().delete()
        DeliverySettlementDetail.objects.bulk_create([
            DeliverySettlementDetail(order=delivery_order, **s)
            for s in settle_data
        ])

        # ── 플랫폼 부가정보 upsert ────────────────────────────
        if baemin_info_data:
            DeliveryBaeminInfo.objects.update_or_create(
                order=delivery_order,
                defaults=baemin_info_data,
            )

        return delivery_order