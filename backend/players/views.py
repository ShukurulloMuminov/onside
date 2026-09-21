from django.shortcuts import get_object_or_404
from rest_framework import permissions, viewsets

from core.permissions import IsSelfOrReadOnly

from .filters import PlayerProfileFilter
from .models import PlayerProfile
from .serializers import PlayerProfileSerializer


class PlayerProfileViewSet(viewsets.ModelViewSet):
    """Public read (per spec: profiles are public pages); only the owning
    user may edit their own profile. Detail lookups accept either the
    internal pk or the public player_id (e.g. "1024" for #1024) so the
    frontend can link straight from "Player ID #1024" without translating
    it first.
    """

    queryset = PlayerProfile.objects.select_related("user").all()
    serializer_class = PlayerProfileSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsSelfOrReadOnly]
    filterset_class = PlayerProfileFilter
    search_fields = ["user__username", "user__first_name", "user__last_name", "city"]
    ordering_fields = ["goals_total", "assists_total", "matches_total", "rating_avg", "created_at"]
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        lookup = self.kwargs[self.lookup_url_kwarg or self.lookup_field]
        pk = PlayerProfile.pk_from_player_id(lookup)
        obj = get_object_or_404(self.get_queryset(), pk=pk)
        self.check_object_permissions(self.request, obj)
        return obj
