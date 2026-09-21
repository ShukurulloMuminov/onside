from rest_framework.exceptions import PermissionDenied, ValidationError

from notifications.models import Notification
from notifications.services import notify

from .models import Badge, Level, PlayerBadge


def compute_level_points(player) -> int:
    """Single formula converting a player's cached career stats into a
    level-progression score. Deliberately separate from
    stats.services.RankingService's leaderboard formula — level is about
    lifetime career progression, ranking is a comparative leaderboard;
    they're free to diverge even though both start from the same stats.
    """
    return (
        player.goals_total * 4
        + player.assists_total * 2
        + player.wins_total * 1
        + player.mvp_total * 3
        + player.matches_total * 1
    )


def get_level_for_player(player) -> Level | None:
    points = compute_level_points(player)
    return Level.objects.filter(required_points__lte=points).order_by("-required_points").first()


def award_badge(*, badge: Badge, player, acting_user) -> PlayerBadge:
    if not acting_user.is_superuser:
        raise PermissionDenied("Only a Super Admin can award badges.")
    if PlayerBadge.objects.filter(badge=badge, player=player).exists():
        raise ValidationError({"player": "This player already has this badge."})
    player_badge = PlayerBadge.objects.create(badge=badge, player=player, awarded_by=acting_user)
    notify(
        recipient=player.user,
        type=Notification.Type.BADGE_EARNED,
        message=f'Siz "{badge.name}" nishonini qo\'lga kiritdingiz!',
        link=f"/players/{player.player_id}",
    )
    return player_badge


def revoke_badge(*, badge: Badge, player, acting_user) -> None:
    if not acting_user.is_superuser:
        raise PermissionDenied("Only a Super Admin can revoke badges.")
    deleted, _ = PlayerBadge.objects.filter(badge=badge, player=player).delete()
    if not deleted:
        raise ValidationError({"player": "This player does not have this badge."})
