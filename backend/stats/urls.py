from django.urls import path

from .views import PlayerRankingsView

urlpatterns = [
    path("players/", PlayerRankingsView.as_view(), name="rankings-players"),
]
