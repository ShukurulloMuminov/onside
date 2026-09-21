from django.db import transaction
from rest_framework.exceptions import PermissionDenied, ValidationError

from notifications.models import Notification
from notifications.services import notify, notify_many
from tournaments.services import require_tournament_admin

from .models import Match, MatchConfirmation


def _captained_registration(match: Match, acting_user):
    """The TournamentRegistration (home or away) whose team acting_user
    captains, or None if they captain neither side of this match."""
    for registration in (match.home_registration, match.away_registration):
        if registration and registration.team.captain_id and registration.team.captain.user_id == acting_user.id:
            return registration
    return None


def _notify_finished(match: Match) -> None:
    recipients = [
        reg.team.captain.user
        for reg in (match.home_registration, match.away_registration)
        if reg and reg.team.captain_id
    ]
    notify_many(
        recipients=recipients,
        type=Notification.Type.MATCH_RESULT,
        message=(
            f"{match.home_registration.team.name} {match.home_score} - {match.away_score} "
            f"{match.away_registration.team.name}: natija yakunlandi."
        ),
        link=f"/matches/{match.id}",
    )


def _notify_disputed(match: Match) -> None:
    admins = match.tournament.admin_roles.select_related("user")
    notify_many(
        recipients=[admin_role.user for admin_role in admins],
        type=Notification.Type.MATCH_DISPUTED,
        message=(
            f"{match.home_registration.team.name} - {match.away_registration.team.name} "
            "o'yini natijasi rad etildi, qayta ko'rib chiqing."
        ),
        link=f"/matches/{match.id}",
    )


@transaction.atomic
def submit_result(
    *, match: Match, home_score, away_score, penalty_home_score=None, penalty_away_score=None, acting_user
) -> Match:
    """Tournament-admin-only entry point for recording a result. If the
    tournament requires captain confirmation the match goes to
    PENDING_CONFIRMATION and waits on confirm_result(); otherwise it's
    finished immediately, matching pre-confirmation-feature behavior."""
    require_tournament_admin(match.tournament, acting_user)
    if match.home_registration_id is None or match.away_registration_id is None:
        raise ValidationError("Both teams must be set before a result can be submitted.")

    match.home_score = home_score
    match.away_score = away_score
    match.penalty_home_score = penalty_home_score
    match.penalty_away_score = penalty_away_score
    # A resubmitted result (correction) invalidates any prior confirmations.
    match.confirmations.all().delete()
    match.status = (
        Match.Status.PENDING_CONFIRMATION
        if match.tournament.require_match_confirmation
        else Match.Status.FINISHED
    )
    match.save()
    if match.status == Match.Status.FINISHED:
        _notify_finished(match)
    return match


@transaction.atomic
def confirm_result(*, match: Match, acting_user) -> Match:
    """Either captain confirming is enough to finish the match — waiting
    on both sides would stall on whichever captain has no reason to
    bother (usually the winner). A captain who disagrees uses
    dispute_result() instead of just not confirming."""
    if match.status != Match.Status.PENDING_CONFIRMATION:
        raise ValidationError("This match is not awaiting confirmation.")

    registration = _captained_registration(match, acting_user)
    if registration is None:
        raise PermissionDenied("Only a captain of one of the two teams can confirm this result.")

    MatchConfirmation.objects.get_or_create(
        match=match, team_registration=registration, defaults={"confirmed_by": acting_user}
    )
    match.status = Match.Status.FINISHED
    match.save()
    _notify_finished(match)
    return match


@transaction.atomic
def dispute_result(*, match: Match, acting_user) -> Match:
    """A captain (typically the losing side) rejects the submitted
    result — throws it back to the tournament admin rather than silently
    letting it sit. Clears the score and confirmations so the admin
    resubmits a corrected result."""
    if match.status != Match.Status.PENDING_CONFIRMATION:
        raise ValidationError("This match is not awaiting confirmation.")

    registration = _captained_registration(match, acting_user)
    if registration is None:
        raise PermissionDenied("Only a captain of one of the two teams can dispute this result.")

    _notify_disputed(match)
    match.confirmations.all().delete()
    match.home_score = None
    match.away_score = None
    match.penalty_home_score = None
    match.penalty_away_score = None
    match.status = Match.Status.SCHEDULED
    match.save()
    return match


@transaction.atomic
def force_finalize(*, match: Match, acting_user) -> Match:
    """Tournament-admin override for a pending-confirmation match stuck on
    an unresponsive captain (no-show)."""
    require_tournament_admin(match.tournament, acting_user)
    if match.home_score is None or match.away_score is None:
        raise ValidationError("Submit a result before finalizing.")
    match.status = Match.Status.FINISHED
    match.save()
    _notify_finished(match)
    return match
