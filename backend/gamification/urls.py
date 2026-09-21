from rest_framework.routers import DefaultRouter

from .views import BadgeViewSet, LevelViewSet

router = DefaultRouter()
router.register("levels", LevelViewSet, basename="level")
router.register("badges", BadgeViewSet, basename="badge")

urlpatterns = router.urls
