from django.contrib import admin

from .models import PlayerMatchStats, TeamMatchStats

admin.site.register(PlayerMatchStats)
admin.site.register(TeamMatchStats)
