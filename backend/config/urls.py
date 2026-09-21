from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/auth/", include("accounts.urls")),
    path("api/v1/players/", include("players.urls")),
    path("api/v1/teams/", include("teams.urls")),
    path("api/v1/tournaments/", include("tournaments.urls")),
    path("api/v1/matches/", include("matches.urls")),
    path("api/v1/rankings/", include("stats.urls")),
    path("api/v1/", include("gamification.urls")),
    path("api/v1/notifications/", include("notifications.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
