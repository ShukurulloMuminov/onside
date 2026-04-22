from django.urls import path
from . import views

urlpatterns = [
    path('', views.TeamListCreateView.as_view(), name='team-list'),
    path('my-teams/', views.MyTeamsView.as_view(), name='my-teams'),
    path('my-invitations/', views.MyInvitationsView.as_view(), name='my-invitations'),
    path('invitations/<int:invitation_id>/respond/', views.InvitationResponseView.as_view(), name='invitation-respond'),

    path('<int:pk>/', views.TeamDetailView.as_view(), name='team-detail'),
    path('<int:pk>/members/', views.TeamMembersView.as_view(), name='team-members'),
    path('<int:pk>/members/<int:player_id>/', views.TeamMemberRemoveView.as_view(), name='team-member-remove'),
    path('<int:pk>/change-captain/', views.TeamChangeCaptainView.as_view(), name='team-change-captain'),
    path('<int:pk>/invite/', views.TeamInvitationSendView.as_view(), name='team-invite'),
]
