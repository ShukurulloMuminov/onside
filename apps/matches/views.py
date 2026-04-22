from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from .models import Match, MatchEvent, PlayerMatchStat
from .serializers import (
    MatchListSerializer,
    MatchDetailSerializer,
    MatchCreateUpdateSerializer,
    MatchEventSerializer,
    MatchEventCreateSerializer,
    PlayerMatchStatSerializer,
    PlayerMatchStatBulkSerializer,
    MatchScoreUpdateSerializer,
    MatchStatusSerializer,
)
from apps.accounts.permissions import IsTournamentAdmin
from apps.accounts.models import User


def is_match_admin(user, match):
    """Foydalanuvchi bu o'yin admini yoki umumiy admimi?"""
    return (
        user.role in ['superadmin', 'tournament_admin'] or
        match.match_admin == user
    )


class MatchListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/matches/      - Barcha o'yinlar (public)
    POST /api/v1/matches/      - O'yin yaratish (admin)
    """
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['tournament', 'status', 'stage', 'home_team', 'away_team']
    search_fields = ['home_team__name', 'away_team__name', 'location']
    ordering_fields = ['match_date', 'created_at']

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsTournamentAdmin()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MatchCreateUpdateSerializer
        return MatchListSerializer

    def get_queryset(self):
        qs = Match.objects.select_related('home_team', 'away_team', 'tournament')
        tournament_id = self.request.query_params.get('tournament_id')
        if tournament_id:
            qs = qs.filter(tournament_id=tournament_id)
        return qs


class MatchDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/matches/{id}/   - O'yin ma'lumotlari (public)
    PUT    /api/v1/matches/{id}/   - Yangilash (admin)
    DELETE /api/v1/matches/{id}/   - O'chirish (admin)
    """
    queryset = Match.objects.prefetch_related('events', 'player_stats__player')

    def get_permissions(self):
        if self.request.method == 'GET':
            return [permissions.AllowAny()]
        return [IsTournamentAdmin()]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return MatchCreateUpdateSerializer
        return MatchDetailSerializer


class MatchScoreView(APIView):
    """
    POST /api/v1/matches/{id}/score/
    O'yin hisobini yangilash (match admin yoki turnir admin)
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            match = Match.objects.get(pk=pk)
        except Match.DoesNotExist:
            return Response({'error': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if not is_match_admin(request.user, match):
            return Response({'error': 'Ruxsat yo\'q'}, status=status.HTTP_403_FORBIDDEN)

        serializer = MatchScoreUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        match.home_score = serializer.validated_data['home_score']
        match.away_score = serializer.validated_data['away_score']
        if 'status' in serializer.validated_data:
            match.status = serializer.validated_data['status']
        match.save()

        return Response({
            'message': 'Hisob yangilandi',
            'home_score': match.home_score,
            'away_score': match.away_score,
            'status': match.status
        })


class MatchStatusView(APIView):
    """
    POST /api/v1/matches/{id}/status/
    O'yin statusini o'zgartirish
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            match = Match.objects.get(pk=pk)
        except Match.DoesNotExist:
            return Response({'error': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if not is_match_admin(request.user, match):
            return Response({'error': 'Ruxsat yo\'q'}, status=status.HTTP_403_FORBIDDEN)

        serializer = MatchStatusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        match.status = serializer.validated_data['status']
        match.save()
        return Response({'message': f'Status "{match.get_status_display()}" ga o\'zgartirildi'})


# ============================================================
# O'YIN VOQEALARI (GOL, ASSIST, KARTALAR)
# ============================================================

class MatchEventListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/matches/{id}/events/   - O'yin voqealari (public)
    POST /api/v1/matches/{id}/events/   - Voqea qo'shish (match admin)
    """
    def get_permissions(self):
        if self.request.method == 'POST':
            return [permissions.IsAuthenticated()]
        return [permissions.AllowAny()]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return MatchEventCreateSerializer
        return MatchEventSerializer

    def get_queryset(self):
        return MatchEvent.objects.filter(match_id=self.kwargs['pk']).select_related('player', 'team')

    def create(self, request, *args, **kwargs):
        try:
            match = Match.objects.get(pk=kwargs['pk'])
        except Match.DoesNotExist:
            return Response({'error': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if not is_match_admin(request.user, match):
            return Response({'error': 'Ruxsat yo\'q'}, status=status.HTTP_403_FORBIDDEN)

        serializer = MatchEventCreateSerializer(data=request.data, context={'match': match})
        serializer.is_valid(raise_exception=True)
        event = serializer.save(match=match, created_by=request.user)

        # GOL kiritilganda hisob va statistikani yangilash
        if event.event_type == 'goal':
            if event.team == match.home_team:
                match.home_score += 1
            else:
                match.away_score += 1
            match.save()
            self._update_player_stat(match, event.player, event.team, 'goals')

        elif event.event_type == 'own_goal':
            # O'z darvozasiga gol - raqib jamoasiga gol
            if event.team == match.home_team:
                match.away_score += 1
            else:
                match.home_score += 1
            match.save()

        elif event.event_type == 'assist':
            self._update_player_stat(match, event.player, event.team, 'assists')

        elif event.event_type == 'yellow_card':
            self._update_player_stat(match, event.player, event.team, 'yellow_cards')

        elif event.event_type == 'red_card':
            self._update_player_stat(match, event.player, event.team, 'red_cards')

        return Response(MatchEventSerializer(event).data, status=status.HTTP_201_CREATED)

    def _update_player_stat(self, match, player, team, field):
        stat, _ = PlayerMatchStat.objects.get_or_create(
            match=match, player=player,
            defaults={'team': team}
        )
        setattr(stat, field, getattr(stat, field) + 1)
        stat.save()


class MatchEventDeleteView(APIView):
    """
    DELETE /api/v1/matches/{id}/events/{event_id}/
    Voqeani o'chirish (hisob ham tuzatiladi)
    """
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk, event_id):
        try:
            match = Match.objects.get(pk=pk)
            event = MatchEvent.objects.get(pk=event_id, match=match)
        except (Match.DoesNotExist, MatchEvent.DoesNotExist):
            return Response({'error': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if not is_match_admin(request.user, match):
            return Response({'error': 'Ruxsat yo\'q'}, status=status.HTTP_403_FORBIDDEN)

        # Gol o'chirilganda hisobni kamaytirish
        if event.event_type == 'goal':
            if event.team == match.home_team and match.home_score > 0:
                match.home_score -= 1
            elif event.team == match.away_team and match.away_score > 0:
                match.away_score -= 1
            match.save()
            stat = PlayerMatchStat.objects.filter(match=match, player=event.player).first()
            if stat and stat.goals > 0:
                stat.goals -= 1
                stat.save()

        event.delete()
        return Response({'message': 'Voqea o\'chirildi'})


# ============================================================
# O'YINCHI STATISTIKASI KIRITISH
# ============================================================

class PlayerMatchStatListView(generics.ListAPIView):
    """
    GET /api/v1/matches/{id}/stats/
    O'yindagi barcha o'yinchilar statistikasi (public)
    """
    serializer_class = PlayerMatchStatSerializer
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        return PlayerMatchStat.objects.filter(
            match_id=self.kwargs['pk']
        ).select_related('player', 'team')


class PlayerMatchStatCreateUpdateView(APIView):
    """
    POST /api/v1/matches/{id}/stats/
    O'yinchi statistikasini kiritish/yangilash (match admin)
    Bir yoki bir necha o'yinchi statistikasi kiritiladi
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            match = Match.objects.get(pk=pk)
        except Match.DoesNotExist:
            return Response({'error': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if not is_match_admin(request.user, match):
            return Response({'error': 'Ruxsat yo\'q'}, status=status.HTTP_403_FORBIDDEN)

        # Bitta o'yinchi statistikasi
        player_id = request.data.get('player_id')
        team_id = request.data.get('team')

        if not player_id or not team_id:
            return Response({'error': 'player_id va team majburiy'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            player = User.objects.get(pk=player_id)
            from apps.teams.models import Team
            team = Team.objects.get(pk=team_id)
        except (User.DoesNotExist, Exception):
            return Response({'error': 'O\'yinchi yoki jamoa topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        stat, created = PlayerMatchStat.objects.update_or_create(
            match=match,
            player=player,
            defaults={
                'team': team,
                'goals': request.data.get('goals', 0),
                'assists': request.data.get('assists', 0),
                'yellow_cards': request.data.get('yellow_cards', 0),
                'red_cards': request.data.get('red_cards', 0),
                'minutes_played': request.data.get('minutes_played', 0),
                'is_starting': request.data.get('is_starting', True),
            }
        )

        return Response({
            'message': 'Statistika ' + ('yaratildi' if created else 'yangilandi'),
            'stat': PlayerMatchStatSerializer(stat).data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class BulkPlayerStatView(APIView):
    """
    POST /api/v1/matches/{id}/stats/bulk/
    Barcha o'yinchilar statistikasini bir vaqtda kiritish
    Body: { "stats": [ {player_id, team, goals, assists, ...}, ... ] }
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            match = Match.objects.get(pk=pk)
        except Match.DoesNotExist:
            return Response({'error': 'Topilmadi'}, status=status.HTTP_404_NOT_FOUND)

        if not is_match_admin(request.user, match):
            return Response({'error': 'Ruxsat yo\'q'}, status=status.HTTP_403_FORBIDDEN)

        stats_data = request.data.get('stats', [])
        if not stats_data:
            return Response({'error': 'stats bo\'sh'}, status=status.HTTP_400_BAD_REQUEST)

        results = []
        errors = []

        for item in stats_data:
            try:
                player = User.objects.get(pk=item['player_id'])
                from apps.teams.models import Team
                team = Team.objects.get(pk=item['team'])

                stat, created = PlayerMatchStat.objects.update_or_create(
                    match=match,
                    player=player,
                    defaults={
                        'team': team,
                        'goals': item.get('goals', 0),
                        'assists': item.get('assists', 0),
                        'yellow_cards': item.get('yellow_cards', 0),
                        'red_cards': item.get('red_cards', 0),
                        'minutes_played': item.get('minutes_played', 0),
                        'is_starting': item.get('is_starting', True),
                    }
                )
                results.append(PlayerMatchStatSerializer(stat).data)
            except Exception as e:
                errors.append({'player_id': item.get('player_id'), 'error': str(e)})

        return Response({
            'saved': len(results),
            'errors': errors,
            'stats': results
        })
