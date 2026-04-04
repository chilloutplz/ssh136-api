# config/urls.py
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    path("api/accounts/", include("accounts.urls")),
    path("api/organization/", include("organization.urls")),    # 회사(내부 조직)
    path("api/product/", include("product.urls")),              # 품목(판매, 구매)
    path("api/party/", include("party.urls")),                  # 거래처(판매처, 구매처)
    path("api/purchase/", include("purchase.urls")),
    path("api/sales/", include("sale.urls")),
    path("api/inventory/", include("inventory.urls")),
]