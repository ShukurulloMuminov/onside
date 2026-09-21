from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from core.permissions import IsTournamentAdminOfObject

from . import services as match_services
from .models import Match, MatchEvent
from .serializers import (
    MatchEventCreateSerializer,
    MatchEventSerializer,
    MatchResultSubmitSerializer,
    MatchSerializer,
)


class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.select_related(
        "home_registration__team", "away_registration__team", "tournament"
    ).prefetch_related("events__player__user", "confirmations")
    serializer_class = MatchSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]
    filterset_fields = ["status", "tournament"]
    ordering_fields = ["scheduled_date", "scheduled_time", "created_at"]
    ordering = ["-scheduled_date", "-scheduled_time"]

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.AllowAny()]
        # confirm/dispute are open to any authenticated user —
        # matches.services enforces that only a captain of one of the two
        # teams can act, since a tournament admin's blanket object
        # permission doesn't apply to team captains.
        if self.action in ("confirm", "dispute"):
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsTournamentAdminOfObject()]

    def perform_create(self, serializer):
        tournament = serializer.validated_data["tournament"]
        from tournaments.services import require_tournament_admin

        require_tournament_admin(tournament, self.request.user)
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"], url_path="submit-result")
    def submit_result(self, request: Request, pk=None) -> Response:
        match = self.get_object()
        serializer = MatchResultSubmitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        match = match_services.submit_result(match=match, acting_user=request.user, **serializer.validated_data)
        return Response(MatchSerializer(match).data)

    @action(detail=True, methods=["post"], url_path="confirm")
    def confirm(self, request: Request, pk=None) -> Response:
        match = self.get_object()
        match = match_services.confirm_result(match=match, acting_user=request.user)
        return Response(MatchSerializer(match).data)

    @action(detail=True, methods=["post"], url_path="dispute")
    def dispute(self, request: Request, pk=None) -> Response:
        match = self.get_object()
        match = match_services.dispute_result(match=match, acting_user=request.user)
        return Response(MatchSerializer(match).data)

    @action(detail=True, methods=["post"], url_path="force-finalize")
    def force_finalize(self, request: Request, pk=None) -> Response:
        match = self.get_object()
        match = match_services.force_finalize(match=match, acting_user=request.user)
        return Response(MatchSerializer(match).data)

    @action(detail=True, methods=["post"], url_path="events")
    def add_event(self, request: Request, pk=None) -> Response:
        match = self.get_object()
        serializer = MatchEventCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        event = serializer.save(match=match, created_by=request.user)
        return Response(MatchEventSerializer(event).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["delete"], url_path=r"events/(?P<event_id>\d+)")
    def remove_event(self, request: Request, pk=None, event_id=None) -> Response:
        match = self.get_object()
        event = get_object_or_404(MatchEvent, pk=event_id, match=match)
        event.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
