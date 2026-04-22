from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    # Auth
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Profile
    path('me/', views.MyProfileView.as_view(), name='my-profile'),
    path('change-password/', views.ChangePasswordView.as_view(), name='change-password'),

    # Public
    path('players/', views.PublicPlayerListView.as_view(), name='player-list'),
    path('players/<int:pk>/', views.PublicPlayerDetailView.as_view(), name='player-detail'),

    # Admin
    path('admin/users/', views.AdminUserListCreateView.as_view(), name='admin-user-list'),
    path('admin/users/<int:pk>/', views.AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('admin/users/<int:pk>/reset-password/', views.AdminResetPasswordView.as_view(), name='admin-reset-password'),
]
