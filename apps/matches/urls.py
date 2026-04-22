from django.urls import path
from . import views

urlpatterns = [
    path('', views.MatchListCreateView.as_view(), name='match-list'),
    path('<int:pk>/', views.MatchDetailView.as_view(), name='match-detail'),
    path('<int:pk>/score/', views.MatchScoreView.as_view(), name='match-score'),
    path('<int:pk>/status/', views.MatchStatusView.as_view(), name='match-status'),

    # Voqealar
    path('<int:pk>/events/', views.MatchEventListCreateView.as_view(), name='match-events'),
    path('<int:pk>/events/<int:event_id>/', views.MatchEventDeleteView.as_view(), name='match-event-delete'),

    # Statistika
    path('<int:pk>/stats/', views.PlayerMatchStatListView.as_view(), name='match-stats-list'),
    path('<int:pk>/stats/add/', views.PlayerMatchStatCreateUpdateView.as_view(), name='match-stats-add'),
    path('<int:pk>/stats/bulk/', views.BulkPlayerStatView.as_view(), name='match-stats-bulk'),
]
