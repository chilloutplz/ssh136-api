from rest_framework.viewsets import ModelViewSet
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import Product, BOM
from .serializers import ProductSerializer, BOMSerializer
from core.utils.db_utils import reset_id_sequence 


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all().order_by("name")
    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_active", "is_resell", "base_unit", "purchase_unit", "sales_unit"]
    search_fields = ["name", "code", "spec"]
    ordering_fields = ["name", "code", "created_at", "updated_at"]

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        # 상품 삭제 후 PK 시퀀스 재설정
        reset_id_sequence(Product._meta.db_table)


class BOMViewSet(ModelViewSet):
    queryset = BOM.objects.select_related("parent", "component").all()
    serializer_class = BOMSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["parent", "component", "is_active"]
    search_fields = ["parent__name", "component__name", "parent__code", "component__code"]
    ordering_fields = ["created_at", "updated_at", "quantity"]

    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        # BOM 삭제 후 PK 시퀀스 재설정
        reset_id_sequence(BOM._meta.db_table)