from rest_framework.routers import DefaultRouter

from .views import PlayerProfileViewSet

router = DefaultRouter()
router.register("", PlayerProfileViewSet, basename="player")

urlpatterns = router.urls
