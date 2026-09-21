from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response

from core.permissions import IsTeamCaptain
from players.models import PlayerProfile

from . import services
from .formations import DEFAULT_FORMATION_BY_SIZE
from .models import Team, TeamInvitation
from .serializers import (
    InvitePlayerSerializer,
    SetTeamLineupSerializer,
    TeamInvitationSerializer,
    TeamLineupSerializer,
    TeamMembershipSerializer,
    TeamSerializer,
)


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.select_related("captain__user").all()
    serializer_class = TeamSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsTeamCaptain]
    lookup_field = "slug"
    search_fields = ["name", "city"]
    ordering_fields = ["wins_total", "goals_for_total", "trophies_total", "created_at"]
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]

    def get_permissions(self):
        if self.action in ("list", "retrieve", "members"):
            return [permissions.AllowAny()]
        if self.action == "lineup" and self.request.method == "GET":
            return [permissions.AllowAny()]
        return super().get_permissions()

    def perform_create(self, serializer):
        try:
            creator = self.request.user.player_profile
        except PlayerProfile.DoesNotExist as exc:
            raise ValidationError(
                "You need a player profile before creating a team."
            ) from exc
        team = services.create_team(creator=creator, **serializer.validated_data)
        serializer.instance = team

    @action(detail=True, methods=["get"])
    def members(self, request: Request, slug=None) -> Response:
        team = self.get_object()
        memberships = team.memberships.filter(is_active=True).select_related("player__user")
        return Response(TeamMembershipSerializer(memberships, many=True).data)

    @action(detail=True, methods=["post"])
    def invite(self, request: Request, slug=None) -> Response:
        team = self.get_object()
        serializer = InvitePlayerSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        invitation = services.invite_player(
            team=team, acting_user=request.user, player_id=serializer.validated_data["player_id"]
        )
        return Response(TeamInvitationSerializer(invitation).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get", "patch"], url_path="lineup")
    def lineup(self, request: Request, slug=None) -> Response:
        team = self.get_object()

        if request.method == "GET":
            lineup_obj = getattr(team, "lineup", None)
            if lineup_obj is None:
                return Response({"formation": DEFAULT_FORMATION_BY_SIZE[team.squad_size], "slots": []})
            return Response(TeamLineupSerializer(lineup_obj).data)

        serializer = SetTeamLineupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lineup_obj = services.set_team_lineup(
            team=team,
            acting_user=request.user,
            formation=serializer.validated_data["formation"],
            assignments=serializer.validated_data["assignments"],
        )
        return Response(TeamLineupSerializer(lineup_obj).data)


class MyInvitationsView(viewsets.ReadOnlyModelViewSet):
    serializer_class = TeamInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return TeamInvitation.objects.none()
        return TeamInvitation.objects.filter(
            invited_player__user=self.request.user
        ).select_related("team__captain__user", "invited_player__user")

    @action(detail=True, methods=["post"])
    def accept(self, request: Request, pk=None) -> Response:
        invitation = get_object_or_404(TeamInvitation, pk=pk)
        invitation = services.respond_to_invitation(
            invitation=invitation, acting_user=request.user, accept=True
        )
        return Response(TeamInvitationSerializer(invitation).data)

    @action(detail=True, methods=["post"])
    def reject(self, request: Request, pk=None) -> Response:
        invitation = get_object_or_404(TeamInvitation, pk=pk)
        invitation = services.respond_to_invitation(
            invitation=invitation, acting_user=request.user, accept=False
        )
        return Response(TeamInvitationSerializer(invitation).data)
