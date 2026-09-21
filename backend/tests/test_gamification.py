import pytest
from rest_framework.exceptions import PermissionDenied, ValidationError

from gamification import services as gamification_services
from gamification.models import Badge, Level, PlayerBadge

pytestmark = pytest.mark.django_db


@pytest.fixture
def levels(db):
    Level.objects.all().delete()
    return [
        Level.objects.create(order=1, name="Rookie", required_points=0),
        Level.objects.create(order=2, name="Player", required_points=50),
        Level.objects.create(order=3, name="Legend", required_points=200),
    ]


@pytest.fixture
def badge(db):
    return Badge.objects.create(name="Top Scorer", icon="🔥")


def test_compute_level_points_uses_the_documented_formula(make_player):
    player = make_player("scorer")
    player.goals_total = 5
    player.assists_total = 2
    player.wins_total = 3
    player.mvp_total = 1
    player.matches_total = 4
    player.save()

    # 5*4 + 2*2 + 3*1 + 1*3 + 4*1 = 20 + 4 + 3 + 3 + 4 = 34
    assert gamification_services.compute_level_points(player) == 34


def test_get_level_for_player_picks_highest_threshold_met(make_player, levels):
    player = make_player("leveled")
    player.goals_total = 100  # comfortably over the "Legend" threshold
    player.save()

    level = gamification_services.get_level_for_player(player)

    assert level.name == "Legend"


def test_get_level_for_player_with_zero_stats_gets_lowest_level(make_player, levels):
    player = make_player("newbie")

    level = gamification_services.get_level_for_player(player)

    assert level.name == "Rookie"


def test_superuser_can_award_and_revoke_badge(make_player, make_superuser, badge):
    admin = make_superuser()
    player = make_player("awardee")

    player_badge = gamification_services.award_badge(badge=badge, player=player, acting_user=admin)
    assert isinstance(player_badge, PlayerBadge)
    assert PlayerBadge.objects.filter(badge=badge, player=player).exists()

    gamification_services.revoke_badge(badge=badge, player=player, acting_user=admin)
    assert not PlayerBadge.objects.filter(badge=badge, player=player).exists()


def test_non_superuser_cannot_award_badge(make_player, badge):
    bystander = make_player("bystander")

    with pytest.raises(PermissionDenied):
        gamification_services.award_badge(badge=badge, player=bystander, acting_user=bystander.user)


def test_cannot_award_same_badge_twice(make_player, make_superuser, badge):
    admin = make_superuser()
    player = make_player("double_awardee")
    gamification_services.award_badge(badge=badge, player=player, acting_user=admin)

    with pytest.raises(ValidationError):
        gamification_services.award_badge(badge=badge, player=player, acting_user=admin)


def test_revoking_badge_player_does_not_have_raises(make_player, make_superuser, badge):
    admin = make_superuser()
    player = make_player("never_awarded")

    with pytest.raises(ValidationError):
        gamification_services.revoke_badge(badge=badge, player=player, acting_user=admin)
