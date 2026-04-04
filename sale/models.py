from django.db import models
from core.models.base import BaseModel


class Store(BaseModel):
    """
    매장 (MATE POS 기준).
    Sale 에서 store_code/store_name 중복을 제거하기 위해 분리.
    """
    code = models.CharField("매장코드", max_length=20, unique=True)
    name = models.CharField("매장명", max_length=100)

    class Meta:
        verbose_name = "매장"
        verbose_name_plural = "매장"

    def __str__(self):
        return f"[{self.code}] {self.name}"


class Sale(BaseModel):
    """
    주문 단건 트랜잭션 (MATE POS 상세 API 기준).
    결제취소 건 포함 → payment_status 로 구분.
    """

    class PaymentStatus(models.TextChoices):
        COMPLETED = '결제완료', '결제완료'
        CANCELLED = '결제취소', '결제취소'

    CHANNEL_CHOICES = [
        ('HALL',    '홀'),
        ('BAEMIN',  '배민'),
        ('COUPANG', '쿠팡'),
        ('YOGIYO',  '요기요'),
        ('DDANGYO', '땡겨요'),
        ('KARROT',  '당근'),
    ]

    # ── 데이터 출처 / 원본 ────────────────────────────────────
    source   = models.CharField("데이터 출처", max_length=20, default="matepos", db_index=True)
    raw_data = models.JSONField("원본 데이터", null=True, blank=True)

    # ── 매장 ─────────────────────────────────────────────────
    # store_code 로 get_or_create → FK 연결
    store = models.ForeignKey(
        Store, on_delete=models.PROTECT,
        related_name="sales", verbose_name="매장"
    )

    # ── 날짜/시간 ─────────────────────────────────────────────
    business_date = models.DateField("영업일", db_index=True)
    sold_at       = models.DateTimeField("주문일시", null=True, blank=True, db_index=True)

    # ── 주문 식별 ─────────────────────────────────────────────
    order_seq        = models.PositiveSmallIntegerField("주문번호(일련)")
    # 배달 플랫폼 주문번호 (displayChannelOrderNo) — 배민: T2BK0001TC0J 형태
    channel_order_no = models.CharField("채널 주문번호", max_length=100, null=True, blank=True, db_index=True)

    # ── 주문 분류 ─────────────────────────────────────────────
    order_category = models.CharField("주문구분", max_length=10)       # 온라인 / 오프라인
    channel        = models.CharField(
        "채널", max_length=20, choices=CHANNEL_CHOICES, default='HALL', db_index=True
    )
    channel_detail = models.CharField("주문채널상세", max_length=20)   # 배민1, 요기배달 …
    order_type     = models.CharField("주문타입", max_length=10)       # 배달 / 내점 / 포장

    # ── 결제 ─────────────────────────────────────────────────
    payment_status   = models.CharField(
        "결제상태", max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.COMPLETED,
        db_index=True,
    )
    payment_method   = models.CharField("결제수단", max_length=20)     # 복합 / 카드 / 선결제
    delivery_company = models.CharField("배달업체", max_length=20, null=True, blank=True)

    # ── 금액 (원화 정수) ─────────────────────────────────────
    sale_amount          = models.IntegerField("판매금액", default=0)
    discount_amount      = models.IntegerField("할인금액", default=0)
    net_sale_amount      = models.IntegerField("매출(취소)금액", default=0)
    channel_delivery_fee = models.IntegerField("채널배달료(매출제외)", default=0)
    channel_discount     = models.IntegerField("채널할인(매출제외)", default=0)
    actual_sale_amount   = models.IntegerField("실매출액", default=0)
    taxable_amount       = models.IntegerField("과세금액", default=0)
    vat                  = models.IntegerField("부가세", default=0)
    non_taxable_amount   = models.IntegerField("비과세금액", default=0)
    cup_deposit          = models.IntegerField("일회용컵보증금", default=0)
    online_delivery_fee  = models.IntegerField("온라인채널 배달료", default=0)

    # ── 반품/취소 원본 주문 참조 ──────────────────────────────
    # 반품 건은 처리일에 별도 행으로 생성됨.
    # 원래 주문과 연결하기 위해 orgOperDt, orgBillNo 저장.
    # 집계 시 반품 건을 원래 영업일로 귀속시킬 때 사용.
    org_business_date = models.DateField("원래 영업일", null=True, blank=True)
    org_order_seq     = models.CharField("원래 주문번호", max_length=20, null=True, blank=True)

    # ── 기타 ─────────────────────────────────────────────────
    mate_qr_order_no = models.CharField("MATE QR 주문번호", max_length=100, null=True, blank=True)
    note             = models.TextField("메모", blank=True, null=True)

    class Meta:
        verbose_name = "주문"
        verbose_name_plural = "주문"
        unique_together = [('store', 'business_date', 'order_seq')]
        ordering = ['-business_date', '-order_seq']
        indexes = [
            models.Index(fields=['business_date', 'channel']),
            models.Index(fields=['business_date', 'payment_status']),
        ]

    def __str__(self):
        return f"[{self.get_channel_display()}] {self.business_date} #{self.order_seq} {self.actual_sale_amount:,}원"

    @property
    def is_cancelled(self):
        return self.payment_status == self.PaymentStatus.CANCELLED


class SaleItem(BaseModel):
    """
    주문 상품 내역 (MATE POS 상세 API items[]).
    배달비(DLV00), 채널할인(DSC00) 같은 가상 항목도 포함.
    saleExceptYn='Y' 인 항목은 매출 집계에서 제외.
    Product FK 없음 — goodsCd/goodsNm 으로 직접 관리.
    """

    sale     = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items", verbose_name="주문")
    item_seq = models.PositiveSmallIntegerField("항목순번")

    # ── 상품 ─────────────────────────────────────────────────
    goods_cd = models.CharField("상품코드", max_length=50)
    goods_nm = models.CharField("상품명", max_length=200)

    # ── 금액 ─────────────────────────────────────────────────
    app_prc    = models.IntegerField("적용단가", default=0)
    sale_qty   = models.IntegerField("수량", default=0)
    sale_amt   = models.IntegerField("판매금액", default=0)
    item_dc_amt = models.IntegerField("항목할인", default=0)
    taxable_amount = models.IntegerField("과세금액", default=0)
    vat        = models.IntegerField("부가세", default=0)
    non_taxable_amount = models.IntegerField("비과세금액", default=0)
    sale_except_amt = models.IntegerField("매출제외금액", default=0)  # 채널할인 등

    # ── 플래그 ────────────────────────────────────────────────
    # Y = 배달비·채널할인 등 매출 제외 항목
    sale_except_yn = models.CharField("매출제외여부", max_length=1, default='N')
    packing_yn     = models.CharField("포장여부", max_length=1, default='N')

    # ── 옵션/세트 원본 (중첩 구조 → JSON 보관) ─────────────────
    item_details     = models.JSONField("세트구성", default=list, blank=True)
    item_opt_details = models.JSONField("옵션구성", default=list, blank=True)

    class Meta:
        ordering = ['sale', 'item_seq']
        verbose_name = "주문 상품"
        verbose_name_plural = "주문 상품"
        unique_together = [('sale', 'item_seq')]

    def __str__(self):
        return f"{self.goods_nm} x {self.sale_qty} ({self.sale_amt:,}원)"

    @property
    def subtotal(self):
        return self.sale_amt - self.item_dc_amt


class SaleTender(BaseModel):
    """
    결제 수단별 내역 (MATE POS 상세 API tenders[]).
    복합결제 시 여러 행으로 분리됨.
    예) 선결제 32,700 + 채널할인(즉시) 2,000 + 배달앱할인 1,000
    """

    sale       = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="tenders", verbose_name="주문")
    tender_seq = models.PositiveSmallIntegerField("결제순번")

    # ── 결제수단 ──────────────────────────────────────────────
    # tenderCd 원본값 그대로 (PREPAID, CARD, IMMEDDSC, CHANNELDSC, CASH 등)
    tender_cd  = models.CharField("결제수단코드", max_length=30)
    tender_nm  = models.CharField("결제수단명", max_length=50)   # msTenderNm

    # ── 금액 ─────────────────────────────────────────────────
    tender_amt = models.IntegerField("결제금액", default=0)
    change_amt = models.IntegerField("거스름돈", default=0)

    # ── 플래그 ────────────────────────────────────────────────
    pre_tender_yn = models.CharField("선결제여부", max_length=1, default='N')
    return_yn     = models.CharField("반환여부", max_length=1, default='N')

    # ── 카드 승인 정보 (현장카드 결제 시) ─────────────────────
    approval_no = models.CharField("승인번호", max_length=50, null=True, blank=True)
    approval_dt = models.CharField("승인일시", max_length=20, null=True, blank=True)
    pur_nm      = models.CharField("카드사명", max_length=50, null=True, blank=True)

    class Meta:
        ordering = ['sale', 'tender_seq']
        verbose_name = "결제 수단"
        verbose_name_plural = "결제 수단"
        unique_together = [('sale', 'tender_seq')]

    def __str__(self):
        return f"{self.tender_nm} {self.tender_amt:,}원"


class DeliveryOrderExtra(BaseModel):
    """배달 플랫폼 주문 부가 정보 및 정산 요약"""
    sale = models.OneToOneField('Sale', on_delete=models.CASCADE, related_name="delivery_extra")
    deposit_due_amount = models.IntegerField("입금예정금액", default=0)
    deposit_due_date = models.DateField("입금예정일", null=True, blank=True)
    pay_type = models.CharField("결제타입", max_length=20, null=True, blank=True)
    receive_type = models.CharField("수령방법", max_length=20, null=True, blank=True)

    class Meta:
        verbose_name = "배달 주문 부가정보"

class DeliveryOrderItem(BaseModel):
    # 기존 SaleItem과 연결 (연결 안 될 경우를 대비해 null=True)
    sale_item = models.OneToOneField('SaleItem', on_delete=models.CASCADE, related_name="delivery_item", null=True)
    # POS와 별개로 배민에서 내려온 원본 메뉴명 저장
    menu_name = models.CharField("배민 메뉴명", max_length=200)
    quantity = models.IntegerField("수량", default=1)
    price = models.IntegerField("단가", default=0)
    # 사장님이 강조하신 품목별 할인액
    discount_price = models.IntegerField("품목할인금액", default=0)

    class Meta:
        verbose_name = "배달 주문 품목"

class DeliveryOrderItemOption(BaseModel):
    delivery_item = models.ForeignKey(DeliveryOrderItem, on_delete=models.CASCADE, related_name="options")
    option_name = models.CharField("옵션명", max_length=100)
    option_price = models.IntegerField("옵션금액", default=0)
    option_discount_price = models.IntegerField("옵션할인금액", default=0)

class DeliverySettlementDetail(BaseModel):
    """배달 플랫폼 정산 세부 내역 (항목별 쪼개기)"""
    sale = models.ForeignKey('Sale', on_delete=models.CASCADE, related_name="settlement_details")
    category = models.CharField("정산분류", max_length=50)
    item_name = models.CharField("항목명", max_length=100)
    amount = models.IntegerField("금액")
    api_code = models.CharField("항목코드", max_length=50, null=True, blank=True)

    class Meta:
        verbose_name = "배달 정산 상세"
    """
    일별 정산 — 배달 플랫폼 수수료 (스크래핑).
    매출 합계는 Sale.actual_sale_amount 집계로 계산.
    """

    date = models.DateField("날짜", unique=True, db_index=True)

    # ── 배민 ──────────────────────────────────────────────────
    baemin_commission_fee = models.DecimalField("배민 중개수수료",  max_digits=12, decimal_places=2, default=0)
    baemin_delivery_fee   = models.DecimalField("배민 배달대행비",  max_digits=12, decimal_places=2, default=0)
    baemin_ad_fee         = models.DecimalField("배민 광고비",      max_digits=12, decimal_places=2, default=0)
    baemin_vat            = models.DecimalField("배민 VAT",         max_digits=12, decimal_places=2, default=0)
    baemin_other_fee      = models.DecimalField("배민 기타수수료",   max_digits=12, decimal_places=2, default=0)

    # ── 쿠팡 ──────────────────────────────────────────────────
    coupang_commission_fee = models.DecimalField("쿠팡 중개수수료", max_digits=12, decimal_places=2, default=0)
    coupang_delivery_fee   = models.DecimalField("쿠팡 배달대행비", max_digits=12, decimal_places=2, default=0)
    coupang_ad_fee         = models.DecimalField("쿠팡 광고비",     max_digits=12, decimal_places=2, default=0)
    coupang_other_fee      = models.DecimalField("쿠팡 기타수수료",  max_digits=12, decimal_places=2, default=0)

    # ── 요기요 ────────────────────────────────────────────────
    yogiyo_commission_fee = models.DecimalField("요기요 중개수수료", max_digits=12, decimal_places=2, default=0)
    yogiyo_delivery_fee   = models.DecimalField("요기요 배달대행비", max_digits=12, decimal_places=2, default=0)

    class Meta:
        ordering = ["-date"]
        verbose_name = "일별 정산"
        verbose_name_plural = "일별 정산"

    def __str__(self):
        return f"{self.date} 정산"

    # ── 채널별 매출 ───────────────────────────────────────────
    def _channel_sales(self, channel: str) -> int:
        from django.db.models import Sum
        result = Sale.objects.filter(
            business_date=self.date,
            channel=channel,
            payment_status=Sale.PaymentStatus.COMPLETED,
        ).aggregate(total=Sum('actual_sale_amount'))
        return result['total'] or 0

    @property
    def hall_sales(self):
        return self._channel_sales('HALL')

    @property
    def baemin_sales(self):
        return self._channel_sales('BAEMIN')

    @property
    def coupang_sales(self):
        return self._channel_sales('COUPANG')

    @property
    def yogiyo_sales(self):
        return self._channel_sales('YOGIYO')

    # ── 수수료 합계 ───────────────────────────────────────────
    @property
    def baemin_total_fee(self):
        return (self.baemin_commission_fee + self.baemin_delivery_fee +
                self.baemin_ad_fee + self.baemin_vat + self.baemin_other_fee)

    @property
    def coupang_total_fee(self):
        return (self.coupang_commission_fee + self.coupang_delivery_fee +
                self.coupang_ad_fee + self.coupang_other_fee)

    @property
    def yogiyo_total_fee(self):
        return self.yogiyo_commission_fee + self.yogiyo_delivery_fee

    @property
    def total_fee(self):
        return self.baemin_total_fee + self.coupang_total_fee + self.yogiyo_total_fee

    # ── 순수입 ────────────────────────────────────────────────
    @property
    def baemin_net(self):
        return self.baemin_sales - self.baemin_total_fee

    @property
    def coupang_net(self):
        return self.coupang_sales - self.coupang_total_fee

    @property
    def yogiyo_net(self):
        return self.yogiyo_sales - self.yogiyo_total_fee

    # ── 전체 합계 ─────────────────────────────────────────────
    @property
    def total_sales(self):
        return self.hall_sales + self.baemin_sales + self.coupang_sales + self.yogiyo_sales

    @property
    def net_income(self):
        return self.total_sales - self.total_fee

    @property
    def fee_rate(self):
        if self.total_sales > 0:
            return (self.total_fee / self.total_sales) * 100
        return 0