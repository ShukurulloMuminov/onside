from django.urls import path
from . import views

urlpatterns = [
    # O'yinchi statistikasi
    path('players/<int:player_id>/', views.PlayerProfileStatsView.as_view(), name='player-stats'),
    path('my-stats/', views.MyStatsView.as_view(), name='my-stats'),

    # Reytinglar
    path('top-scorers/', views.TopScorersView.as_view(), name='top-scorers'),
    path('top-assists/', views.TopAssistsView.as_view(), name='top-assists'),
    path('leaderboard/', views.GlobalLeaderboardView.as_view(), name='leaderboard'),

    # Jamoalar
    path('teams/', views.TeamStatsView.as_view(), name='team-stats'),

    # Turnir umumiy
    path('tournament/<int:tournament_id>/summary/', views.TournamentSummaryView.as_view(), name='tournament-summary'),
]
