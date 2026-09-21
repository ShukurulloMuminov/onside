from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import permissions
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from tournaments.models import Tournament

from .services import RankingService


class PlayerRankingsView(APIView):
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter("scope", str, description="'global' or 'tournament'"),
            OpenApiParameter("tournament", str, description="Tournament slug, required when scope=tournament"),
            OpenApiParameter("limit", int, description="Max rows to return (default 50)"),
        ],
        responses={200: dict},
    )
    def get(self, request: Request) -> Response:
        scope = request.query_params.get("scope", "global")
        tournament = None
        if scope == "tournament":
            tournament_slug = request.query_params.get("tournament")
            tournament = get_object_or_404(Tournament, slug=tournament_slug)
        limit = int(request.query_params.get("limit", 50))
        rankings = RankingService.get_player_rankings(scope=scope, tournament=tournament, limit=limit)
        return Response(rankings)
