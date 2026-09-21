from rest_framework.routers import DefaultRouter

from .views import MyInvitationsView, TeamViewSet

router = DefaultRouter()
router.register("invitations", MyInvitationsView, basename="my-invitation")
router.register("", TeamViewSet, basename="team")

urlpatterns = router.urls
