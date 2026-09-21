from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from accounts.models import User
from core.permissions import IsSuperAdmin, IsTournamentAdminOfObject
from teams.models import Team

from . import services
from .filters import TournamentFilter
from .models import Tournament, TournamentRegistration, TournamentStage
from .serializers import (
    ApplyToTournamentSerializer,
    TournamentRegistrationSerializer,
    TournamentSerializer,
    TournamentStageSerializer,
)

PUBLIC_ACTIONS = {"list", "retrieve", "groups", "standings", "bracket", "matches"}
ADMIN_ONLY_ACTIONS = {"create", "destroy", "assign_admin"}
TOURNAMENT_ADMIN_ACTIONS = {
    "update",
    "partial_update",
    "generate_groups",
    "generate_knockout",
    "registrations",
    "approve_registration",
    "reject_registration",
}


class TournamentViewSet(viewsets.ModelViewSet):
    """Tournament creation is Super-Admin-only: per the spec, a Tournament
    Admin is a role granted by the Super Admin, so the bootstrapping flow
    is "Super Admin creates the tournament + assigns its admin(s)", after
    which that Tournament Admin manages just this tournament via update
    and the registrations/generate-groups actions below.
    """

    queryset = Tournament.objects.all()
    serializer_class = TournamentSerializer
    filterset_class = TournamentFilter
    lookup_field = "slug"
    search_fields = ["name", "city", "organizer"]
    ordering_fields = ["start_date", "created_at"]

    def get_permissions(self):
        if self.action in PUBLIC_ACTIONS:
            return [permissions.AllowAny()]
        if self.action in ADMIN_ONLY_ACTIONS:
            return [IsSuperAdmin()]
        if self.action in TOURNAMENT_ADMIN_ACTIONS:
            return [permissions.IsAuthenticated(), IsTournamentAdminOfObject()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=False, methods=["get"], url_path="mine")
    def mine(self, request: Request) -> Response:
        """Tournaments the current user administers — powers the
        Tournament Admin Dashboard's "your tournaments" list. Super
        admins administer everything, so return the full set for them."""
        if request.user.is_superuser:
            qs = self.get_queryset()
        else:
            qs = request.user.administered_tournaments.all()
        return Response(TournamentSerializer(qs, many=True).data)

    @action(detail=True, methods=["post"], url_path="admins")
    def assign_admin(self, request: Request, slug=None) -> Response:
        tournament = self.get_object()
        user = get_object_or_404(User, pk=request.data.get("user_id"))
        from .models import TournamentAdmin

        TournamentAdmin.objects.get_or_create(
            tournament=tournament, user=user, defaults={"assigned_by": request.user}
        )
        return Response(status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="register")
    def register(self, request: Request, slug=None) -> Response:
        tournament = self.get_object()
        serializer = ApplyToTournamentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        team = get_object_or_404(Team, slug=serializer.validated_data["team_slug"])
        registration = services.apply_to_tournament(
            tournament=tournament, team=team, acting_user=request.user
        )
        return Response(
            TournamentRegistrationSerializer(registration).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["get"], url_path="registrations")
    def registrations(self, request: Request, slug=None) -> Response:
        tournament = self.get_object()
        self.check_object_permissions(request, tournament)
        qs = tournament.registrations.select_related("team__captain__user").all()
        return Response(TournamentRegistrationSerializer(qs, many=True).data)

    @action(
        detail=True,
        methods=["post"],
        url_path=r"registrations/(?P<registration_id>\d+)/approve",
    )
    def approve_registration(self, request: Request, slug=None, registration_id=None) -> Response:
        tournament = self.get_object()
        self.check_object_permissions(request, tournament)
        registration = get_object_or_404(
            TournamentRegistration, pk=registration_id, tournament=tournament
        )
        registration = services.review_registration(
            registration=registration, acting_user=request.user, approve=True
        )
        return Response(TournamentRegistrationSerializer(registration).data)

    @action(
        detail=True,
        methods=["post"],
        url_path=r"registrations/(?P<registration_id>\d+)/reject",
    )
    def reject_registration(self, request: Request, slug=None, registration_id=None) -> Response:
        tournament = self.get_object()
        self.check_object_permissions(request, tournament)
        registration = get_object_or_404(
            TournamentRegistration, pk=registration_id, tournament=tournament
        )
        registration = services.review_registration(
            registration=registration, acting_user=request.user, approve=False
        )
        return Response(TournamentRegistrationSerializer(registration).data)

    @action(detail=True, methods=["post"], url_path="generate-groups")
    def generate_groups(self, request: Request, slug=None) -> Response:
        tournament = self.get_object()
        self.check_object_permissions(request, tournament)
        stage = services.generate_groups(tournament=tournament, acting_user=request.user)
        return Response(TournamentStageSerializer(stage).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"], url_path="generate-knockout")
    def generate_knockout(self, request: Request, slug=None) -> Response:
        tournament = self.get_object()
        self.check_object_permissions(request, tournament)
        from stats.services import KnockoutService

        stage = KnockoutService.generate_bracket(tournament=tournament, acting_user=request.user)
        return Response(TournamentStageSerializer(stage).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"], url_path="groups")
    def groups(self, request: Request, slug=None) -> Response:
        tournament = self.get_object()
        stages = tournament.stages.filter(type=TournamentStage.Type.GROUP).prefetch_related(
            "groups__memberships__registration__team"
        )
        return Response(TournamentStageSerializer(stages, many=True).data)

    @action(detail=True, methods=["get"], url_path="standings")
    def standings(self, request: Request, slug=None) -> Response:
        tournament = self.get_object()
        from stats.services import StandingsService

        return Response(StandingsService.get_tournament_standings(tournament))

    @action(detail=True, methods=["get"], url_path="bracket")
    def bracket(self, request: Request, slug=None) -> Response:
        tournament = self.get_object()
        from stats.services import KnockoutService

        return Response(KnockoutService.get_bracket(tournament))

    @action(detail=True, methods=["get"], url_path="matches")
    def matches(self, request: Request, slug=None) -> Response:
        tournament = self.get_object()
        from matches.serializers import MatchSerializer

        qs = tournament.matches.select_related(
            "home_registration__team", "away_registration__team"
        ).order_by("scheduled_date", "scheduled_time")
        return Response(MatchSerializer(qs, many=True).data)
