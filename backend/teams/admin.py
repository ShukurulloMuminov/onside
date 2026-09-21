from django.contrib import admin

from .models import Team, TeamInvitation, TeamLineup, TeamLineupSlot, TeamMembership


class TeamMembershipInline(admin.TabularInline):
    model = TeamMembership
    extra = 0


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "captain", "city", "wins_total", "tournaments_total")
    search_fields = ("name", "city")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [TeamMembershipInline]
    # trophies_total is intentionally editable: there's no automated
    # "tournament winner" award flow yet (that's the MVP2 badge system),
    # so a Super Admin bumps it by hand when a tournament concludes.
    readonly_fields = (
        "matches_total",
        "wins_total",
        "draws_total",
        "losses_total",
        "goals_for_total",
        "goals_against_total",
        "tournaments_total",
    )


@admin.register(TeamInvitation)
class TeamInvitationAdmin(admin.ModelAdmin):
    list_display = ("team", "invited_player", "status", "created_at", "responded_at")
    list_filter = ("status",)


class TeamLineupSlotInline(admin.TabularInline):
    model = TeamLineupSlot
    extra = 0


@admin.register(TeamLineup)
class TeamLineupAdmin(admin.ModelAdmin):
    list_display = ("team", "formation")
    inlines = [TeamLineupSlotInline]
