from django.db import models
from core.models.base import BaseModel
from sale.models import Sale


class DeliveryOrder(BaseModel):
    """
    배달 플랫폼 주문 헤더 (배민/쿠팡/요기요 공통).
    Sale 과는 channel_order_no 로 매칭.
    정산 완료된 건만 저장 (NOT_READY 제외).
    """

    class Platform(models.TextChoices):
        BAEMIN  = 'BAEMIN',  '배달의민족'
        COUPANG = 'COUPANG', '쿠팡이츠'
        YOGIYO  = 'YOGIYO',  '요기요'

    # ── MATE POS 연결 ─────────────────────────────────────────
    # channel_order_no 기준 매칭. POS에 없는 주문도 있을 수 있어 nullable.
    sale = models.OneToOneField(
        Sale,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name="delivery_order",
        verbose_name="POS 주문",
    )

    # ── 플랫폼 ───────────────────────────────────────────────
    platform     = models.CharField("플랫폼", max_length=10, choices=Platform.choices, db_index=True)
    order_number = models.CharField("플랫폼 주문번호", max_length=100, unique=True, db_index=True)

    # ── 주문 기본 ────────────────────────────────────────────
    order_datetime   = models.DateTimeField("주문일시")
    status           = models.CharField("주문상태", max_length=20)        # CLOSED 등
    delivery_type    = models.CharField("배달유형", max_length=20)        # DELIVERY 등
    pay_type         = models.CharField("결제유형", max_length=20)        # BARO(선결제) 등
    pay_amount       = models.IntegerField("고객결제금액", default=0)
    items_summary    = models.CharField("주문메뉴요약", max_length=200, blank=True)

    # ── 정산 ─────────────────────────────────────────────────
    deposit_due_amount = models.IntegerField("최종정산금", default=0)
    deposit_due_date   = models.DateField("정산예정일", null=True, blank=True, db_index=True)

    # ── 원본 ─────────────────────────────────────────────────
    raw_data = models.JSONField("원본 데이터", null=True, blank=True)

    class Meta:
        verbose_name = "배달 주문"
        verbose_name_plural = "배달 주문"
        ordering = ['-order_datetime']
        indexes = [
            models.Index(fields=['platform', 'order_datetime']),
            models.Index(fields=['platform', 'deposit_due_date']),
        ]

    def __str__(self):
        return f"[{self.platform}] {self.order_number} {self.deposit_due_amount:,}원"


class DeliveryOrderItem(BaseModel):
    """배달 주문 메뉴 항목"""

    order    = models.ForeignKey(DeliveryOrder, on_delete=models.CASCADE, related_name="items", verbose_name="주문")
    item_seq = models.PositiveSmallIntegerField("항목순번")
    name     = models.CharField("메뉴명", max_length=200)
    quantity = models.IntegerField("수량", default=1)
    total_price   = models.IntegerField("금액", default=0)
    discount_price = models.IntegerField("할인금액", default=0)

    class Meta:
        verbose_name = "배달 주문 메뉴"
        verbose_name_plural = "배달 주문 메뉴"
        ordering = ['order', 'item_seq']
        unique_together = [('order', 'item_seq')]

    def __str__(self):
        return f"{self.name} x {self.quantity}"


class DeliveryOrderItemOption(BaseModel):
    """배달 주문 메뉴 옵션"""

    item  = models.ForeignKey(DeliveryOrderItem, on_delete=models.CASCADE, related_name="options", verbose_name="메뉴")
    name  = models.CharField("옵션명", max_length=200, blank=True)
    price = models.IntegerField("옵션금액", default=0)

    class Meta:
        verbose_name = "배달 주문 옵션"
        verbose_name_plural = "배달 주문 옵션"
        ordering = ['item']

    def __str__(self):
        return f"{self.name} {self.price:,}원"


class DeliverySettlementDetail(BaseModel):
    """
    정산 항목 상세 (플랫폼 공통).
    code/name/amount 구조로 플랫폼 무관하게 저장.

    배민 코드 예시:
      ORDER_AMOUNT       주문금액
      ADVERTISE_FEE      중개이용료
      DISCOUNT_AMOUNT    고객할인비용
      DELIVERY_SUPPLY_PRICE  배달비
      SERVICE_FEE        결제정산수수료
    """

    class GroupType(models.TextChoices):
        ORDER    = 'ORDER',    '주문'
        DELIVERY = 'DELIVERY', '배달'
        ETC      = 'ETC',      '기타'

    order    = models.ForeignKey(DeliveryOrder, on_delete=models.CASCADE, related_name="settlement_details", verbose_name="주문")
    group    = models.CharField("그룹", max_length=10, choices=GroupType.choices)  # ORDER / DELIVERY / ETC
    code     = models.CharField("항목코드", max_length=50)   # ADVERTISE_FEE 등
    name     = models.CharField("항목명", max_length=100)    # 중개이용료 등
    amount   = models.IntegerField("금액", default=0)        # 음수 = 차감

    class Meta:
        verbose_name = "정산 상세"
        verbose_name_plural = "정산 상세"
        ordering = ['order', 'group']

    def __str__(self):
        return f"{self.name} {self.amount:,}원"


class DeliveryBaeminInfo(BaseModel):
    """
    배민 전용 부가 정보.
    공통 모델에 없는 배민 고유 필드 저장.
    """

    order = models.OneToOneField(
        DeliveryOrder,
        on_delete=models.CASCADE,
        related_name="baemin_info",
        verbose_name="배달 주문",
    )

    # ── 광고/채널 ────────────────────────────────────────────
    ad_campaign_key  = models.CharField("광고유형", max_length=30, blank=True)  # BAEMIN_1_PLUS / OPEN_LIST
    is_club_member   = models.BooleanField("배민클럽 여부", default=False)
    delivery_carry_type = models.CharField("배달방식", max_length=20, blank=True)  # SINGLE / COMMON

    # ── 할인 ─────────────────────────────────────────────────
    shop_discount          = models.IntegerField("사장님부담 할인", default=0)
    order_instant_discount = models.IntegerField("주문 즉시할인", default=0)
    total_instant_discount = models.IntegerField("전체 즉시할인", default=0)

    # ── 정산 ─────────────────────────────────────────────────
    order_brokerage_amount = models.IntegerField("주문정산금", default=0)
    delivery_item_amount   = models.IntegerField("배달비정산", default=0)
    etc_item_amount        = models.IntegerField("기타정산", default=0)
    deduction_vat          = models.IntegerField("공제VAT", default=0)

    class Meta:
        verbose_name = "배민 주문 정보"
        verbose_name_plural = "배민 주문 정보"

    def __str__(self):
        return f"{self.order.order_number} 배민 정보"