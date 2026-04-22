from django.contrib import admin
from .models import Team, TeamMembership, TeamInvitation


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'short_name', 'captain', 'city', 'players_count', 'is_active', 'created_at']
    list_filter = ['is_active', 'city']
    search_fields = ['name', 'short_name']


@admin.register(TeamMembership)
class TeamMembershipAdmin(admin.ModelAdmin):
    list_display = ['team', 'player', 'role', 'jersey_number', 'is_active', 'joined_at']
    list_filter = ['role', 'is_active', 'team']
    search_fields = ['player__username', 'team__name']


@admin.register(TeamInvitation)
class TeamInvitationAdmin(admin.ModelAdmin):
    list_display = ['team', 'invited_player', 'invited_by', 'status', 'created_at']
    list_filter = ['status']
