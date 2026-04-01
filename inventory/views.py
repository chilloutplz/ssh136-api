from rest_framework.viewsets import ModelViewSet
from .models import Warehouse, Stock, StockTransaction
from .serializers import WarehouseSerializer, StockSerializer, StockTransactionSerializer

class WarehouseViewSet(ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer

class StockViewSet(ModelViewSet):
    queryset = Stock.objects.select_related("product", "warehouse")
    serializer_class = StockSerializer

class StockTransactionViewSet(ModelViewSet):
    queryset = StockTransaction.objects.select_related("product", "warehouse")
    serializer_class = StockTransactionSerializer