from rest_framework.routers import DefaultRouter
from .views import WarehouseViewSet, StockViewSet, StockTransactionViewSet

router = DefaultRouter()
router.register(r'warehouses', WarehouseViewSet)
router.register(r'stocks', StockViewSet)
router.register(r'stock-transactions', StockTransactionViewSet)

urlpatterns = router.urls