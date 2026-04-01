from rest_framework.viewsets import ModelViewSet
from .models import Account, JournalEntry, JournalLine
from .serializers import AccountSerializer, JournalEntrySerializer, JournalLineSerializer

class AccountViewSet(ModelViewSet):
    queryset = Account.objects.all()
    serializer_class = AccountSerializer

class JournalEntryViewSet(ModelViewSet):
    queryset = JournalEntry.objects.prefetch_related("lines")
    serializer_class = JournalEntrySerializer

class JournalLineViewSet(ModelViewSet):
    queryset = JournalLine.objects.select_related("account", "entry")
    serializer_class = JournalLineSerializer