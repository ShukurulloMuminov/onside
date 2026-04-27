from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import serializers
from django.db.models import Sum, Count, Q, F

from apps.matches.models import PlayerMatchStat, Match
from apps.accounts.models import User
from apps.teams.models import Team
from apps.tournaments.models import Tournament


# ============================================================
# SERIALIZERS
# ============================================================

class PlayerOverallStatSerializer(serializers.Serializer):
    """O'yinchining umumiy karyera statistikasi"""
    player_id = serializers.IntegerField()
    username = serializers.CharField()
    full_name = serializers.CharField()
    avatar = serializers.ImageField()
    position = serializers.CharField()
    matches_played = serializers.IntegerField()
    goals = serializers.IntegerField()
    assists = serializers.IntegerField()
    yellow_cards = serializers.IntegerField()
    red_cards = serializers.IntegerField()
    minutes_played = serializers.IntegerField()


class TopScorerSerializer(serializers.Serializer):
    player_id = serializers.IntegerField()
    username = serializers.CharField()
    full_name = serializers.CharField()
    avatar = serializers.ImageField(allow_null=True)
    team_name = serializers.CharField()
    goals = serializers.IntegerField()
    assists = serializers.IntegerField()
    matches_played = serializers.IntegerField()


class TeamStatSerializer(serializers.Serializer):
    team_id = serializers.IntegerField()
    team_name = serializers.CharField()
    team_logo = serializers.ImageField(allow_null=True)
    matches_played = serializers.IntegerField()
    wins = serializers.IntegerField()
    draws = serializers.IntegerField()
    losses = serializers.IntegerField()
    goals_for = serializers.IntegerField()
    goals_against = serializers.IntegerField()
    goal_difference = serializers.IntegerField()
    points = serializers.IntegerField()


# ============================================================
# VIEWS
# ============================================================

class PlayerProfileStatsView(APIView):
    """
    GET /api/v1/statistics/players/{player_id}/
    O'yinchining to'liq profil statistikasi (barcha turnirlar bo'yicha)
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, player_id):
        try:
            player = User.objects.get(pk=player_id)
        except User.DoesNotExist:
            return Response({'error': 'O\'yinchi topilmadi'}, status=404)

        stats = PlayerMatchStat.objects.filter(player=player)
        agg = stats.aggregate(
            matches=Count('id'),
            goals=Sum('goals'),
            assists=Sum('assists'),
            yellow_cards=Sum('yellow_cards'),
            red_cards=Sum('red_cards'),
            minutes=Sum('minutes_played'),
        )

        # Turnirlar bo'yicha breakdown
        tournament_breakdown = []
        tournament_ids = stats.values_list('match__tournament', flat=True).distinct()
        for t_id in tournament_ids:
            t_stats = stats.filter(match__tournament_id=t_id)
            t_agg = t_stats.aggregate(
                goals=Sum('goals'),
                assists=Sum('assists'),
                matches=Count('id'),
                yellow_cards=Sum('yellow_cards'),
                red_cards=Sum('red_cards'),
            )
            try:
                tournament = Tournament.objects.get(pk=t_id)
                tournament_breakdown.append({
                    'tournament_id': t_id,
                    'tournament_name': tournament.name,
                    **{k: v or 0 for k, v in t_agg.items()}
                })
            except Tournament.DoesNotExist:
                pass

        return Response({
            'player': {
                'id': player.id,
                'username': player.username,
                'full_name': player.full_name,
                'avatar': request.build_absolute_uri(player.avatar.url) if player.avatar else None,
                'position': player.position,
            },
            'overall': {
                'matches_played': agg['matches'] or 0,
                'goals': agg['goals'] or 0,
                'assists': agg['assists'] or 0,
                'yellow_cards': agg['yellow_cards'] or 0,
                'red_cards': agg['red_cards'] or 0,
                'minutes_played': agg['minutes'] or 0,
                'goal_contributions': (agg['goals'] or 0) + (agg['assists'] or 0),
            },
            'by_tournament': tournament_breakdown
        })


class TopScorersView(APIView):
    """
    GET /api/v1/statistics/top-scorers/?tournament_id=&limit=10
    Eng ko'p gol urganlar reytingi
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        tournament_id = request.query_params.get('tournament_id')
        limit = min(int(request.query_params.get('limit', 10)), 50)

        qs = PlayerMatchStat.objects.all()
        if tournament_id:
            qs = qs.filter(match__tournament_id=tournament_id)

        top = qs.values(
            'player__id', 'player__username',
            'player__first_name', 'player__last_name',
            'player__avatar', 'team__name'
        ).annotate(
            total_goals=Sum('goals'),
            total_assists=Sum('assists'),
            total_matches=Count('id'),
        ).filter(total_goals__gt=0).order_by('-total_goals', '-total_assists')[:limit]

        results = []
        for item in top:
            results.append({
                'player_id': item['player__id'],
                'username': item['player__username'],
                'full_name': f"{item['player__first_name']} {item['player__last_name']}".strip() or item['player__username'],
                'avatar': request.build_absolute_uri(item['player__avatar']) if item['player__avatar'] else None,
                'team_name': item['team__name'],
                'goals': item['total_goals'],
                'assists': item['total_assists'],
                'matches_played': item['total_matches'],
            })
        return Response(results)


class TopAssistsView(APIView):
    """
    GET /api/v1/statistics/top-assists/?tournament_id=&limit=10
    Eng ko'p assist berganlar reytingi
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        tournament_id = request.query_params.get('tournament_id')
        limit = min(int(request.query_params.get('limit', 10)), 50)

        qs = PlayerMatchStat.objects.all()
        if tournament_id:
            qs = qs.filter(match__tournament_id=tournament_id)

        top = qs.values(
            'player__id', 'player__username',
            'player__first_name', 'player__last_name',
            'player__avatar', 'team__name'
        ).annotate(
            total_assists=Sum('assists'),
            total_goals=Sum('goals'),
            total_matches=Count('id'),
        ).filter(total_assists__gt=0).order_by('-total_assists', '-total_goals')[:limit]

        results = []
        for item in top:
            results.append({
                'player_id': item['player__id'],
                'username': item['player__username'],
                'full_name': f"{item['player__first_name']} {item['player__last_name']}".strip() or item['player__username'],
                'avatar': request.build_absolute_uri(item['player__avatar']) if item['player__avatar'] else None,
                'team_name': item['team__name'],
                'assists': item['total_assists'],
                'goals': item['total_goals'],
                'matches_played': item['total_matches'],
            })
        return Response(results)


class TeamStatsView(APIView):
    """
    GET /api/v1/statistics/teams/?tournament_id=
    Jamoalar statistikasi
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        tournament_id = request.query_params.get('tournament_id')

        matches_qs = Match.objects.filter(status='finished')
        if tournament_id:
            matches_qs = matches_qs.filter(tournament_id=tournament_id)

        team_ids = set()
        for m in matches_qs:
            team_ids.add(m.home_team_id)
            team_ids.add(m.away_team_id)

        results = []
        for team in Team.objects.filter(id__in=team_ids):
            home = matches_qs.filter(home_team=team)
            away = matches_qs.filter(away_team=team)

            mp = home.count() + away.count()
            w = d = l = gf = ga = 0

            for m in home:
                gf += m.home_score
                ga += m.away_score
                if m.home_score > m.away_score: w += 1
                elif m.home_score == m.away_score: d += 1
                else: l += 1

            for m in away:
                gf += m.away_score
                ga += m.home_score
                if m.away_score > m.home_score: w += 1
                elif m.away_score == m.home_score: d += 1
                else: l += 1

            # Default 3-1-0 ball tizimi
            if tournament_id:
                try:
                    t = Tournament.objects.get(pk=tournament_id)
                    pts = w * t.win_points + d * t.draw_points + l * t.loss_points
                except Tournament.DoesNotExist:
                    pts = w * 3 + d * 1
            else:
                pts = w * 3 + d * 1

            results.append({
                'team_id': team.id,
                'team_name': team.name,
                'team_logo': request.build_absolute_uri(team.logo.url) if team.logo else None,
                'matches_played': mp,
                'wins': w,
                'draws': d,
                'losses': l,
                'goals_for': gf,
                'goals_against': ga,
                'goal_difference': gf - ga,
                'points': pts,
            })

        results.sort(key=lambda x: (-x['points'], -x['goal_difference'], -x['goals_for']))
        return Response(results)


class TournamentSummaryView(APIView):
    """
    GET /api/v1/statistics/tournament/{tournament_id}/summary/
    Turnir umumiy statistikasi
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request, tournament_id):
        try:
            tournament = Tournament.objects.get(pk=tournament_id)
        except Tournament.DoesNotExist:
            return Response({'error': 'Topilmadi'}, status=404)

        matches = Match.objects.filter(tournament=tournament)
        finished = matches.filter(status='finished')
        stats = PlayerMatchStat.objects.filter(match__tournament=tournament)

        total_goals = stats.aggregate(t=Sum('goals'))['t'] or 0
        total_assists = stats.aggregate(t=Sum('assists'))['t'] or 0

        # Top scorer
        top_scorer = stats.values(
            'player__username', 'player__first_name', 'player__last_name', 'player__id'
        ).annotate(g=Sum('goals')).order_by('-g').first()

        # Top assister
        top_assister = stats.values(
            'player__username', 'player__first_name', 'player__last_name', 'player__id'
        ).annotate(a=Sum('assists')).order_by('-a').first()

        return Response({
            'tournament': {
                'id': tournament.id,
                'name': tournament.name,
                'status': tournament.status,
                'format': tournament.format,
            },
            'summary': {
                'total_matches': matches.count(),
                'finished_matches': finished.count(),
                'total_goals': total_goals,
                'total_assists': total_assists,
                'teams_count': tournament.registrations.filter(status='approved').count(),
                'avg_goals_per_match': round(total_goals / finished.count(), 2) if finished.count() > 0 else 0,
            },
            'top_scorer': {
                'player_id': top_scorer['player__id'],
                'name': f"{top_scorer['player__first_name']} {top_scorer['player__last_name']}".strip() or top_scorer['player__username'],
                'goals': top_scorer['g'],
            } if top_scorer and top_scorer['g'] else None,
            'top_assister': {
                'player_id': top_assister['player__id'],
                'name': f"{top_assister['player__first_name']} {top_assister['player__last_name']}".strip() or top_assister['player__username'],
                'assists': top_assister['a'],
            } if top_assister and top_assister['a'] else None,
        })


class GlobalLeaderboardView(APIView):
    """
    GET /api/v1/statistics/leaderboard/
    Barcha turnirlar bo'yicha umumiy reyting
    """
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        limit = min(int(request.query_params.get('limit', 20)), 100)

        top = PlayerMatchStat.objects.values(
            'player__id', 'player__username',
            'player__first_name', 'player__last_name', 'player__avatar',
        ).annotate(
            total_goals=Sum('goals'),
            total_assists=Sum('assists'),
            total_matches=Count('id'),
            total_yellow=Sum('yellow_cards'),
            total_red=Sum('red_cards'),
        ).order_by('-total_goals', '-total_assists')[:limit]

        results = []
        for i, item in enumerate(top, 1):
            results.append({
                'rank': i,
                'player_id': item['player__id'],
                'username': item['player__username'],
                'full_name': f"{item['player__first_name']} {item['player__last_name']}".strip() or item['player__username'],
                'avatar': request.build_absolute_uri(item['player__avatar']) if item['player__avatar'] else None,
                'goals': item['total_goals'] or 0,
                'assists': item['total_assists'] or 0,
                'matches_played': item['total_matches'] or 0,
                'goal_contributions': (item['total_goals'] or 0) + (item['total_assists'] or 0),
            })
        return Response(results)

class MyStatsView(APIView):
    """
    GET /api/v1/statistics/my-stats/
    Mening statistikam
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        view = PlayerProfileStatsView()
        view.request = request
        return view.get(request, request.user.id)
