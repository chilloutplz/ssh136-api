from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import SaleSerializer, DeliveryOrderSerializer

class SaleBulkCreateView(APIView):
    """
    POST /api/sales/bulk-create/
    스크래퍼에서 하루치 주문 배열을 한 번에 전송.

    - 입력: Sale 객체 배열 (items[], tenders[] 중첩 포함)
    - 처리: 건별 update_or_create → 재전송 안전
    - 응답: { created, updated, errors? }
    - 에러 있는 건만 207 로 리포트, 나머지는 정상 저장
    """

    def post(self, request):
        records = request.data

        if not isinstance(records, list):
            return Response(
                {"error": "list expected"},
                status=status.HTTP_400_BAD_REQUEST
            )

        created, updated, errors = 0, 0, []

        for i, record in enumerate(records):
            serializer = SaleSerializer(data=record)

            if not serializer.is_valid():
                errors.append({"index": i, "errors": serializer.errors})
                continue

            sale = serializer.save()

            # BaseModel 의 created_at / updated_at 비교로 신규/업데이트 구분
            if sale.created_at == sale.updated_at:
                created += 1
            else:
                updated += 1

        result = {"created": created, "updated": updated}

        if errors:
            result["errors"] = errors
            return Response(result, status=status.HTTP_207_MULTI_STATUS)

        return Response(result, status=status.HTTP_200_OK)
    

class DeliveryOrderBulkCreateView(APIView):
    """
    POST /api/sales/delivery/bulk-create/
    스크래퍼에서 하루치 배달 주문 배열을 한 번에 전송.
 
    - 입력: DeliveryOrder 배열 (items, settlement_details, baemin_info 중첩 포함)
    - 처리: 건별 update_or_create → 재전송 안전
    - Sale 자동 매칭: order_number → Sale.channel_order_no
    - 응답: { created, updated, errors? }
    """
 
    def post(self, request):
        records = request.data
 
        if not isinstance(records, list):
            return Response(
                {"error": "list expected"},
                status=status.HTTP_400_BAD_REQUEST,
            )
 
        created, updated, errors = 0, 0, []
 
        for i, record in enumerate(records):
            serializer = DeliveryOrderSerializer(data=record)
 
            if not serializer.is_valid():
                errors.append({"index": i, "errors": serializer.errors})
                continue
 
            order = serializer.save()
 
            if order.created_at == order.updated_at:
                created += 1
            else:
                updated += 1
 
        result = {"created": created, "updated": updated}
 
        if errors:
            result["errors"] = errors
            return Response(result, status=status.HTTP_207_MULTI_STATUS)
 
        return Response(result, status=status.HTTP_200_OK)