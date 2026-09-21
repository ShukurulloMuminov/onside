from django.contrib import admin

from .models import Match, MatchEvent


class MatchEventInline(admin.TabularInline):
    model = MatchEvent
    extra = 0


@admin.register(Match)
class MatchAdmin(admin.ModelAdmin):
    list_display = (
        "__str__",
        "tournament",
        "status",
        "scheduled_date",
        "home_score",
        "away_score",
    )
    list_filter = ("status", "tournament")
    inlines = [MatchEventInline]


@admin.register(MatchEvent)
class MatchEventAdmin(admin.ModelAdmin):
    list_display = ("match", "type", "player", "minute")
    list_filter = ("type",)
