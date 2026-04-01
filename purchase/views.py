from rest_framework.viewsets import ModelViewSet
from rest_framework.views import APIView
from rest_framework.response import Response

from .models import Purchase, PurchaseItem
from .serializers import PurchaseSerializer, PurchaseItemSerializer
from .utils.pdf_parser import parse_purchase_pdf

class PurchaseViewSet(ModelViewSet):
    queryset = Purchase.objects.select_related("supplier").prefetch_related("items__product")
    serializer_class = PurchaseSerializer

class PurchaseItemViewSet(ModelViewSet):
    queryset = PurchaseItem.objects.select_related("purchase", "product")
    serializer_class = PurchaseItemSerializer

class PurchaseUploadPDFView(APIView):
    """
    PDF를 업로드받아 거래명세 데이터를 추출해 반환
    """
    def post(self, request):
        file = request.FILES.get("pdf")
        if not file:
            return Response({"error": "파일이 없습니다."}, status=400)

        try:
            parsed_data = parse_purchase_pdf(file)
            return Response(parsed_data, status=200)
        except Exception as e:
            return Response({"error": str(e)}, status=500)