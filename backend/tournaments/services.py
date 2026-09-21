import random
import string

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from notifications.models import Notification
from notifications.services import notify, notify_many
from teams.models import Team

from .models import (
    Group,
    GroupMembership,
    Tournament,
    TournamentRegistration,
    TournamentStage,
)


def _require_captain(team: Team, acting_user):
    if team.captain.user_id != acting_user.id:
        raise PermissionDenied("Only the team captain can apply to a tournament.")


def require_tournament_admin(tournament: Tournament, acting_user):
    if acting_user.is_superuser:
        return
    if not tournament.admin_roles.filter(user=acting_user).exists():
        raise PermissionDenied("You do not administer this tournament.")


@transaction.atomic
def apply_to_tournament(*, tournament: Tournament, team: Team, acting_user) -> TournamentRegistration:
    _require_captain(team, acting_user)

    if tournament.status not in (Tournament.Status.REGISTRATION_OPEN,):
        raise ValidationError({"tournament": "Registration is not open for this tournament."})

    if TournamentRegistration.objects.filter(tournament=tournament, team=team).exists():
        raise ValidationError({"team": "This team has already applied to this tournament."})

    return TournamentRegistration.objects.create(
        tournament=tournament, team=team, applied_by=acting_user
    )


@transaction.atomic
def review_registration(
    *, registration: TournamentRegistration, acting_user, approve: bool
) -> TournamentRegistration:
    require_tournament_admin(registration.tournament, acting_user)

    if registration.status != TournamentRegistration.Status.PENDING:
        raise ValidationError({"status": "This registration has already been reviewed."})

    registration.status = (
        TournamentRegistration.Status.APPROVED if approve else TournamentRegistration.Status.REJECTED
    )
    registration.reviewed_by = acting_user
    registration.reviewed_at = timezone.now()
    registration.save(update_fields=["status", "reviewed_by", "reviewed_at", "updated_at"])

    tournament = registration.tournament
    if registration.team.captain_id:
        notify(
            recipient=registration.team.captain.user,
            type=Notification.Type.REGISTRATION_APPROVED if approve else Notification.Type.REGISTRATION_REJECTED,
            message=(
                f'"{tournament.name}" turniriga arizangiz tasdiqlandi.'
                if approve
                else f'"{tournament.name}" turniriga arizangiz rad etildi.'
            ),
            link=f"/tournaments/{tournament.slug}",
        )
    return registration


def _group_names(count: int):
    return list(string.ascii_uppercase[:count])


def _round_robin_pairs(registrations: list):
    """Circle method: returns a list of rounds, each a list of
    (home_registration, away_registration) tuples. Handles odd-sized
    groups by giving one team a bye per round."""
    teams = list(registrations)
    if len(teams) % 2 == 1:
        teams.append(None)
    n = len(teams)
    rounds = []
    for round_num in range(n - 1):
        pairs = []
        for i in range(n // 2):
            home, away = teams[i], teams[n - 1 - i]
            if home is not None and away is not None:
                pairs.append((home, away) if round_num % 2 == 0 else (away, home))
        rounds.append(pairs)
        teams.insert(1, teams.pop())
    return rounds


@transaction.atomic
def generate_groups(*, tournament: Tournament, acting_user) -> TournamentStage:
    """Distributes all APPROVED registrations evenly into
    tournament.groups_count groups and generates a single round-robin
    fixture list (skeleton Match rows, no date/time yet — the Tournament
    Admin schedules those afterward) for each group.
    """
    require_tournament_admin(tournament, acting_user)

    if tournament.groups_count < 1:
        raise ValidationError({"groups_count": "Configure groups_count on the tournament first."})

    registrations = list(
        tournament.registrations.filter(status=TournamentRegistration.Status.APPROVED)
        .select_related("team__captain__user")
    )
    if len(registrations) < tournament.groups_count * 2:
        raise ValidationError({"registrations": "Not enough approved teams to fill the groups."})

    random.shuffle(registrations)

    stage = TournamentStage.objects.create(
        tournament=tournament,
        type=TournamentStage.Type.GROUP,
        name="Group Stage",
        order=0,
    )

    groups = [
        Group.objects.create(stage=stage, name=name) for name in _group_names(tournament.groups_count)
    ]
    for idx, registration in enumerate(registrations):
        group = groups[idx % len(groups)]
        GroupMembership.objects.create(group=group, registration=registration)

    from matches.models import Match  # lazy: avoids a module-load-time import cycle

    for group in groups:
        group_registrations = [
            gm.registration for gm in group.memberships.select_related("registration").all()
        ]
        for round_pairs in _round_robin_pairs(group_registrations):
            for home, away in round_pairs:
                Match.objects.create(
                    tournament=tournament,
                    stage=stage,
                    group=group,
                    home_registration=home,
                    away_registration=away,
                )

    tournament.status = Tournament.Status.IN_PROGRESS
    tournament.save(update_fields=["status", "updated_at"])

    notify_many(
        recipients=[r.team.captain.user for r in registrations if r.team.captain_id],
        type=Notification.Type.TOURNAMENT_STARTED,
        message=f'"{tournament.name}" turniri boshlandi!',
        link=f"/tournaments/{tournament.slug}",
    )
    return stage
