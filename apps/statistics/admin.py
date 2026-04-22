from django.contrib import admin
from .models import PlayerTournamentStat, TeamTournamentStat


@admin.register(PlayerTournamentStat)
class PlayerTournamentStatAdmin(admin.ModelAdmin):
    list_display = ['player', 'tournament', 'team', 'matches_played', 'goals', 'assists']
    list_filter = ['tournament']
    search_fields = ['player__username', 'team__name']


@admin.register(TeamTournamentStat)
class TeamTournamentStatAdmin(admin.ModelAdmin):
    list_display = ['team', 'tournament', 'matches_played', 'wins', 'draws', 'losses', 'points']
    list_filter = ['tournament']
