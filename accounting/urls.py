from rest_framework.routers import DefaultRouter
from .views import AccountViewSet, JournalEntryViewSet, JournalLineViewSet

router = DefaultRouter()
router.register(r'accounts', AccountViewSet)
router.register(r'journal-entries', JournalEntryViewSet)
router.register(r'journal-lines', JournalLineViewSet)

urlpatterns = router.urls