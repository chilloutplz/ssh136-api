# product/urls.py
from rest_framework.routers import DefaultRouter
from .views import ProductViewSet, BOMViewSet

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"bom", BOMViewSet, basename="bom")

urlpatterns = router.urls