from django.urls import path
from .views import SaleBulkCreateView

# 루트 urls.py 에 아래처럼 include 되어 있어야 함:
# path("api/sales/", include("sale.urls"))

urlpatterns = [
    # 스크래퍼 전송 엔드포인트
    path("bulk-create/", SaleBulkCreateView.as_view(), name="sale-bulk-create"),
]