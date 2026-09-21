from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from core.permissions import IsSuperAdmin
from players.models import PlayerProfile

from . import services
from .models import Badge, Level
from .serializers import AwardBadgeSerializer, BadgeSerializer, LevelSerializer


class LevelViewSet(viewsets.ModelViewSet):
    """Public read (levels are shown on every profile); only a Super
    Admin may create/rename/retier levels."""

    queryset = Level.objects.all()
    serializer_class = LevelSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]


class BadgeViewSet(viewsets.ModelViewSet):
    queryset = Badge.objects.all()
    serializer_class = BadgeSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        return [IsSuperAdmin()]

    def _resolve_player(self, request: Request) -> PlayerProfile:
        serializer = AwardBadgeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            pk = PlayerProfile.pk_from_player_id(serializer.validated_data["player_id"])
            return PlayerProfile.objects.get(pk=pk)
        except (ValueError, PlayerProfile.DoesNotExist) as exc:
            raise ValidationError({"player_id": "No player found with that ID."}) from exc

    @action(detail=True, methods=["post"])
    def award(self, request: Request, pk=None) -> Response:
        badge = self.get_object()
        player = self._resolve_player(request)
        services.award_badge(badge=badge, player=player, acting_user=request.user)
        return Response(BadgeSerializer(badge).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def revoke(self, request: Request, pk=None) -> Response:
        badge = self.get_object()
        player = self._resolve_player(request)
        services.revoke_badge(badge=badge, player=player, acting_user=request.user)
        return Response(status=status.HTTP_204_NO_CONTENT)
