from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from notifications.models import Notification
from notifications.services import notify
from players.models import PlayerProfile

from .formations import FORMATIONS_BY_SIZE
from .models import Team, TeamInvitation, TeamLineup, TeamLineupSlot, TeamMembership


@transaction.atomic
def create_team(*, creator: PlayerProfile, **team_fields) -> Team:
    team = Team.objects.create(captain=creator, **team_fields)
    TeamMembership.objects.create(team=team, player=creator, is_active=True)
    return team


@transaction.atomic
def invite_player(*, team: Team, acting_user, player_id: str) -> TeamInvitation:
    if team.captain.user_id != acting_user.id:
        raise PermissionDenied("Only the team captain can invite players.")

    try:
        pk = PlayerProfile.pk_from_player_id(player_id)
        invited_player = PlayerProfile.objects.get(pk=pk)
    except (ValueError, PlayerProfile.DoesNotExist) as exc:
        raise ValidationError({"player_id": "No player found with that ID."}) from exc

    if TeamMembership.objects.filter(team=team, player=invited_player, is_active=True).exists():
        raise ValidationError({"player_id": "Player is already on this team."})

    if TeamInvitation.objects.filter(
        team=team, invited_player=invited_player, status=TeamInvitation.Status.PENDING
    ).exists():
        raise ValidationError({"player_id": "There is already a pending invitation for this player."})

    invitation = TeamInvitation.objects.create(
        team=team, invited_player=invited_player, invited_by=acting_user
    )
    notify(
        recipient=invited_player.user,
        type=Notification.Type.TEAM_INVITE,
        message=f'"{team.name}" jamoasi sizni jamoaga taklif qildi.',
        link="/dashboard",
    )
    return invitation


@transaction.atomic
def respond_to_invitation(*, invitation: TeamInvitation, acting_user, accept: bool) -> TeamInvitation:
    if invitation.invited_player.user_id != acting_user.id:
        raise PermissionDenied("Only the invited player can respond to this invitation.")
    if invitation.status != TeamInvitation.Status.PENDING:
        raise ValidationError({"status": "This invitation has already been responded to."})

    invitation.status = TeamInvitation.Status.ACCEPTED if accept else TeamInvitation.Status.REJECTED
    invitation.responded_at = timezone.now()
    invitation.save(update_fields=["status", "responded_at", "updated_at"])

    if accept:
        TeamMembership.objects.update_or_create(
            team=invitation.team,
            player=invitation.invited_player,
            defaults={"is_active": True, "left_at": None},
        )
    return invitation


@transaction.atomic
def set_team_lineup(*, team: Team, acting_user, formation: str, assignments: dict[str, int | None]) -> TeamLineup:
    """Replaces the team's default starting XI. `assignments` maps slot
    code -> PlayerProfile pk (or None/omitted to leave a slot empty).
    Only the captain may set it, and only active team members may be
    placed in a slot — this isn't a general-purpose squad builder, it's
    specifically "who's on my own team's default XI"."""
    if team.captain.user_id != acting_user.id:
        raise PermissionDenied("Only the team captain can set the starting lineup.")

    formations_for_size = FORMATIONS_BY_SIZE.get(team.squad_size, {})
    valid_codes = formations_for_size.get(formation)
    if valid_codes is None:
        raise ValidationError(
            {"formation": f"{formation!r} is not a valid formation for a {team.squad_size}x{team.squad_size} team."}
        )

    unknown_codes = set(assignments) - set(valid_codes)
    if unknown_codes:
        raise ValidationError({"assignments": f"Invalid slot codes for {formation}: {sorted(unknown_codes)}."})

    player_ids = [pid for pid in assignments.values() if pid is not None]
    if len(player_ids) != len(set(player_ids)):
        raise ValidationError({"assignments": "A player can only fill one slot."})

    active_member_ids = set(
        TeamMembership.objects.filter(team=team, is_active=True).values_list("player_id", flat=True)
    )
    invalid_players = set(player_ids) - active_member_ids
    if invalid_players:
        raise ValidationError({"assignments": f"Not active members of this team: {sorted(invalid_players)}."})

    lineup, _ = TeamLineup.objects.update_or_create(team=team, defaults={"formation": formation})
    lineup.slots.all().delete()
    TeamLineupSlot.objects.bulk_create(
        [
            TeamLineupSlot(lineup=lineup, code=code, player_id=player_id)
            for code, player_id in assignments.items()
            if player_id is not None
        ]
    )
    return lineup
