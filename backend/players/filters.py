import django_filters

from .models import PlayerProfile


class PlayerProfileFilter(django_filters.FilterSet):
    city = django_filters.CharFilter(field_name="city", lookup_expr="iexact")
    position = django_filters.CharFilter(field_name="position", lookup_expr="iexact")
    team = django_filters.CharFilter(method="filter_team")
    min_rating = django_filters.NumberFilter(field_name="rating_avg", lookup_expr="gte")

    class Meta:
        model = PlayerProfile
        fields = ["city", "position", "team", "min_rating"]

    def filter_team(self, queryset, name, value):
        return queryset.filter(
            team_memberships__is_active=True, team_memberships__team__slug=value
        )
