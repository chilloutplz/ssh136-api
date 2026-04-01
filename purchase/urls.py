from rest_framework.routers import DefaultRouter
from django.urls import path
from .views import PurchaseViewSet, PurchaseItemViewSet, PurchaseUploadPDFView

router = DefaultRouter()
router.register(r'purchases', PurchaseViewSet)
router.register(r'purchase-items', PurchaseItemViewSet)

urlpatterns = router.urls + [
    path("purchases/upload-pdf/", PurchaseUploadPDFView.as_view(), name="purchase-upload-pdf"),
]