from django.contrib import admin
from .models import Tournament, TournamentGroup, TournamentRegistration


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    list_display = ['name', 'format', 'status', 'max_teams', 'start_date', 'end_date', 'created_by']
    list_filter = ['status', 'format']
    search_fields = ['name', 'location']
    filter_horizontal = ['admins']


@admin.register(TournamentGroup)
class TournamentGroupAdmin(admin.ModelAdmin):
    list_display = ['tournament', 'name']
    list_filter = ['tournament']


@admin.register(TournamentRegistration)
class TournamentRegistrationAdmin(admin.ModelAdmin):
    list_display = ['team', 'tournament', 'status', 'registered_at']
    list_filter = ['status', 'tournament']
    search_fields = ['team__name']
