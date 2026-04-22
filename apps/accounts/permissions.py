from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """Faqat Super Admin"""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'superadmin'
        )


class IsTournamentAdmin(BasePermission):
    """Turnir Admin yoki Super Admin"""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role in ['superadmin', 'tournament_admin']
        )


class IsPlayer(BasePermission):
    """Ro'yxatdan o'tgan o'yinchi"""
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_authenticated and
            request.user.role == 'player'
        )


class IsOwnerOrAdmin(BasePermission):
    """O'z profili yoki admin"""
    def has_object_permission(self, request, view, obj):
        if request.user.role in ['superadmin', 'tournament_admin']:
            return True
        return obj == request.user or obj.user == request.user
