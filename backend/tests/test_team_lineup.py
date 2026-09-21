import pytest
from rest_framework.exceptions import PermissionDenied, ValidationError

from teams import services as team_services
from teams.models import TeamLineup

pytestmark = pytest.mark.django_db


def _team_with_roster(make_player, n=4):
    captain = make_player("cap")
    team = team_services.create_team(creator=captain, name="Test FC", city="Qarshi")
    members = [captain]
    for i in range(n - 1):
        p = make_player(f"member{i}")
        inv = team_services.invite_player(team=team, acting_user=captain.user, player_id=p.player_id)
        team_services.respond_to_invitation(invitation=inv, acting_user=p.user, accept=True)
        members.append(p)
    return team, captain, members


def test_captain_can_set_lineup(make_player):
    team, captain, members = _team_with_roster(make_player, n=3)

    lineup = team_services.set_team_lineup(
        team=team,
        acting_user=captain.user,
        formation="4-4-2",
        assignments={"GK": members[1].id, "ST1": members[2].id},
    )

    assert lineup.formation == "4-4-2"
    codes = {slot.code: slot.player_id for slot in lineup.slots.all()}
    assert codes == {"GK": members[1].id, "ST1": members[2].id}


def test_non_captain_cannot_set_lineup(make_player):
    team, captain, members = _team_with_roster(make_player, n=2)
    bystander = make_player("bystander")

    with pytest.raises(PermissionDenied):
        team_services.set_team_lineup(
            team=team, acting_user=bystander.user, formation="4-4-2", assignments={}
        )


def test_rejects_non_member_player(make_player):
    team, captain, members = _team_with_roster(make_player, n=2)
    outsider = make_player("outsider")

    with pytest.raises(ValidationError):
        team_services.set_team_lineup(
            team=team, acting_user=captain.user, formation="4-4-2", assignments={"GK": outsider.id}
        )


def test_rejects_duplicate_player_in_two_slots(make_player):
    team, captain, members = _team_with_roster(make_player, n=2)

    with pytest.raises(ValidationError):
        team_services.set_team_lineup(
            team=team,
            acting_user=captain.user,
            formation="4-4-2",
            assignments={"GK": members[1].id, "ST1": members[1].id},
        )


def test_rejects_unknown_slot_code(make_player):
    team, captain, members = _team_with_roster(make_player, n=2)

    with pytest.raises(ValidationError):
        team_services.set_team_lineup(
            team=team, acting_user=captain.user, formation="4-4-2", assignments={"NOT_A_SLOT": members[1].id}
        )


def test_rejects_unknown_formation(make_player):
    team, captain, members = _team_with_roster(make_player, n=2)

    with pytest.raises(ValidationError):
        team_services.set_team_lineup(
            team=team, acting_user=captain.user, formation="5-5-5", assignments={}
        )


def test_rejects_formation_that_does_not_match_squad_size(make_player):
    team, captain, members = _team_with_roster(make_player, n=2)
    team.squad_size = 5
    team.save(update_fields=["squad_size"])

    # "4-4-2" is an 11-a-side formation, not valid for a 5x5 team.
    with pytest.raises(ValidationError):
        team_services.set_team_lineup(
            team=team, acting_user=captain.user, formation="4-4-2", assignments={}
        )


def test_accepts_formation_matching_squad_size(make_player):
    team, captain, members = _team_with_roster(make_player, n=2)
    team.squad_size = 5
    team.save(update_fields=["squad_size"])

    lineup = team_services.set_team_lineup(
        team=team, acting_user=captain.user, formation="2-2", assignments={"FW1": members[1].id}
    )

    assert lineup.formation == "2-2"


def test_resetting_lineup_clears_old_slots(make_player):
    team, captain, members = _team_with_roster(make_player, n=3)
    team_services.set_team_lineup(
        team=team, acting_user=captain.user, formation="4-4-2", assignments={"GK": members[1].id}
    )

    lineup = team_services.set_team_lineup(
        team=team, acting_user=captain.user, formation="4-3-3", assignments={"ST": members[2].id}
    )

    assert TeamLineup.objects.filter(team=team).count() == 1
    codes = {slot.code: slot.player_id for slot in lineup.slots.all()}
    assert codes == {"ST": members[2].id}


def test_changing_squad_size_drops_now_invalid_lineup(make_player):
    team, captain, members = _team_with_roster(make_player, n=3)
    team_services.set_team_lineup(
        team=team, acting_user=captain.user, formation="4-4-2", assignments={"GK": members[1].id}
    )
    assert TeamLineup.objects.filter(team=team).exists()

    team.squad_size = 5
    team.save()

    assert not TeamLineup.objects.filter(team=team).exists()


def test_changing_squad_size_keeps_lineup_when_formation_still_valid(make_player):
    """Edge case: '2-1-1' happens not to collide with any other size's
    formation names in this app, but the check must be based on whether
    the *stored* formation belongs to the *new* squad_size's formation
    set — not just "did squad_size change" — so a same-size no-op update
    doesn't spuriously wipe a valid lineup."""
    team, captain, members = _team_with_roster(make_player, n=2)
    team.squad_size = 5
    team.save(update_fields=["squad_size"])
    team_services.set_team_lineup(
        team=team, acting_user=captain.user, formation="2-1-1", assignments={"GK": members[1].id}
    )

    team.squad_size = 5
    team.save()

    assert TeamLineup.objects.filter(team=team).exists()
