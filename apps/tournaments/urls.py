from django.urls import path
from . import views

urlpatterns = [
    path('', views.TournamentListCreateView.as_view(), name='tournament-list'),
    path('<int:pk>/', views.TournamentDetailView.as_view(), name='tournament-detail'),
    path('<int:pk>/status/', views.TournamentStatusView.as_view(), name='tournament-status'),
    path('<int:pk>/groups/', views.TournamentGroupView.as_view(), name='tournament-groups'),
    path('<int:pk>/standings/', views.TournamentStandingsView.as_view(), name='tournament-standings'),
    path('<int:pk>/registrations/', views.TournamentRegistrationListView.as_view(), name='tournament-registrations'),
    path('<int:pk>/registrations/<int:reg_id>/approve/', views.RegistrationApproveView.as_view(), name='registration-approve'),
]
