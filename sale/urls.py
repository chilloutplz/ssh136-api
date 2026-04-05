# sale/urls.py
from django.urls import path
from .views import SaleBulkCreateView, DeliveryOrderBulkCreateView

# 루트 urls.py 에 아래처럼 include 되어 있어야 함:
# path("api/sales/", include("sale.urls"))

urlpatterns = [
    # 1. MATE POS 매출 데이터 생성 (기본)
    # URL: /api/sales/bulk-create/
    path("bulk-create/", SaleBulkCreateView.as_view(), name="sale-bulk-create"),
    
    # 배달 플랫폼 스크래퍼 전송 엔드포인트
    path("delivery/bulk-create/", DeliveryOrderBulkCreateView.as_view(), name="delivery-order-bulk-create"),
]