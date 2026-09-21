from django.contrib import admin

from .models import (
    Group,
    GroupMembership,
    KnockoutRound,
    Tournament,
    TournamentAdmin,
    TournamentRegistration,
    TournamentRosterPlayer,
    TournamentStage,
)


class TournamentAdminInline(admin.TabularInline):
    model = TournamentAdmin
    extra = 0


@admin.register(Tournament)
class TournamentAdminModel(admin.ModelAdmin):
    list_display = ("name", "slug", "city", "format", "status", "start_date", "end_date")
    list_filter = ("status", "format", "city")
    search_fields = ("name", "city", "organizer")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [TournamentAdminInline]


@admin.register(TournamentRegistration)
class TournamentRegistrationAdmin(admin.ModelAdmin):
    list_display = ("tournament", "team", "status", "reviewed_by", "reviewed_at")
    list_filter = ("status",)


admin.site.register(TournamentRosterPlayer)
admin.site.register(TournamentStage)
admin.site.register(Group)
admin.site.register(GroupMembership)
admin.site.register(KnockoutRound)
