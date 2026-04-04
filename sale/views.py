from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from .serializers import SaleSerializer, DeliverySaleSerializer

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
    

class DeliveryDataCreateView(APIView):
    """
    배달 플랫폼(배민/쿠팡 등) 스크래핑 데이터를 수신하여 
    기존 POS 데이터(Sale)와 매칭 및 확장 정보를 저장하는 API
    """
    def post(self, request, *args, **kwargs):
        # 1. 단건 또는 다건 데이터 대응
        raw_data = request.data
        data_list = raw_data if isinstance(raw_data, list) else [raw_data]

        results = {
            "total_count": len(data_list),
            "success_count": 0,
            "failed_count": 0,
            "errors": []
        }

        for entry in data_list:
            order_no = entry.get("order_number", "알 수 없음")
            
            # 2. DeliverySaleSerializer 사용
            serializer = DeliverySaleSerializer(data=entry)
            
            if serializer.is_valid():
                try:
                    # Serializer 내부의 @transaction.atomic으로 안전하게 저장
                    serializer.save()
                    results["success_count"] += 1
                except Exception as e:
                    # 런타임 에러 처리 (DB 제약 조건 위반 등)
                    results["failed_count"] += 1
                    results["errors"].append({
                        "order_number": order_no,
                        "type": "RuntimeError",
                        "message": str(e)
                    })
            else:
                # 3. 유효성 검사 실패 (POS 주문번호 없음, 필수 필드 누락 등)
                results["failed_count"] += 1
                results["errors"].append({
                    "order_number": order_no,
                    "type": "ValidationError",
                    "details": serializer.errors
                })

        # 4. 응답 상태 결정
        # 모두 성공 시 201, 전체 실패 시 400, 일부 성공/실패 섞이면 207
        if results["success_count"] == len(data_list):
            return Response(results, status=status.HTTP_201_CREATED)
        elif results["success_count"] == 0:
            return Response(results, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response(results, status=status.HTTP_207_MULTI_STATUS)



        
    
