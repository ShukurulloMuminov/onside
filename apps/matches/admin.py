from django.contrib import admin
from .models import Match, MatchEvent, PlayerMatchStat


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'tournament', 'status', 'home_score', 'away_score', 'match_date']
    list_filter = ['status', 'stage', 'tournament']
    search_fields = ['home_team__name', 'away_team__name']
    date_hierarchy = 'match_date'


@admin.register(MatchEvent)
class MatchEventAdmin(admin.ModelAdmin):
    list_display = ['match', 'player', 'team', 'event_type', 'minute']
    list_filter = ['event_type']


@admin.register(PlayerMatchStat)
class PlayerMatchStatAdmin(admin.ModelAdmin):
    list_display = ['player', 'match', 'team', 'goals', 'assists', 'yellow_cards', 'red_cards']
    list_filter = ['team', 'match__tournament']
    search_fields = ['player__username']
