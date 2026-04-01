from rest_framework.viewsets import ModelViewSet
from .models import Party
from .serializers import PartySerializer
from core.utils.db_utils import reset_id_sequence


class PartyViewSet(ModelViewSet):
    queryset = Party.objects.all()
    serializer_class = PartySerializer
    
    def perform_destroy(self, instance):
        super().perform_destroy(instance)
        # 거래처 삭제 후 PK 시퀀스 재설정
        reset_id_sequence(Party._meta.db_table)
