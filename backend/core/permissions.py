from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsSuperAdmin(BasePermission):
    """Platform-wide control. Maps directly onto Django's is_superuser so
    the same account also gets Django admin access."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class IsTournamentAdminOfObject(BasePermission):
    """Object-level check: the requesting user must be listed as an admin
    of *this specific* tournament (via the TournamentAdmin through-table),
    or be a super admin. Resolves the tournament off the object itself,
    or off an object.tournament attribute, so it can guard Tournament,
    Match, MatchEvent, TournamentRegistration, etc. without duplicating
    this class per app.

    Imports tournaments.models lazily to avoid a core <-> tournaments
    circular import at module load time.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        from tournaments.models import Tournament, TournamentAdmin

        tournament = obj if isinstance(obj, Tournament) else getattr(obj, "tournament", None)
        if tournament is None:
            return False
        return TournamentAdmin.objects.filter(tournament=tournament, user=request.user).exists()


class IsTeamCaptain(BasePermission):
    """Object-level check: the requesting user must be the captain of
    *this specific* team, or a super admin."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        from teams.models import Team

        team = obj if isinstance(obj, Team) else getattr(obj, "team", None)
        if team is None or team.captain_id is None:
            return False
        return team.captain.user_id == request.user.id


class IsSelfOrReadOnly(BasePermission):
    """Allows anyone to read; only the owning user (or a super admin) may write."""

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.user.is_superuser:
            return True
        owner_user_id = getattr(obj, "user_id", None) or getattr(obj, "id", None)
        return owner_user_id == request.user.id
