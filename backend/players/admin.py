from django.contrib import admin

from .models import PlayerProfile


@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = (
        "player_id_display",
        "user",
        "city",
        "position",
        "goals_total",
        "assists_total",
        "matches_total",
        "rating_avg",
    )
    list_filter = ("position", "city")
    search_fields = ("user__username", "user__first_name", "user__last_name", "city")
    readonly_fields = (
        "matches_total",
        "wins_total",
        "goals_total",
        "assists_total",
        "mvp_total",
        "yellow_cards_total",
        "red_cards_total",
        "tournaments_total",
        "rating_avg",
    )

    @admin.display(description="Player ID")
    def player_id_display(self, obj):
        return obj.player_id
