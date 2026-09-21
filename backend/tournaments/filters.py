import django_filters

from .models import Tournament


class TournamentFilter(django_filters.FilterSet):
    city = django_filters.CharFilter(field_name="city", lookup_expr="iexact")
    status = django_filters.CharFilter(field_name="status", lookup_expr="iexact")
    format = django_filters.CharFilter(field_name="format", lookup_expr="iexact")

    class Meta:
        model = Tournament
        fields = ["city", "status", "format"]
