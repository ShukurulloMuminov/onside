from rest_framework.routers import DefaultRouter

from .views import TournamentViewSet

router = DefaultRouter()
router.register("", TournamentViewSet, basename="tournament")

urlpatterns = router.urls
