import pytest
from rest_framework.exceptions import PermissionDenied, ValidationError

from teams import services as team_services
from teams.models import TeamInvitation, TeamMembership

pytestmark = pytest.mark.django_db


def test_create_team_makes_creator_captain_and_member(make_player):
    captain = make_player("captain")
    team = team_services.create_team(creator=captain, name="Qarshi FC", city="Qarshi")

    assert team.captain_id == captain.id
    assert TeamMembership.objects.filter(team=team, player=captain, is_active=True).exists()


def test_invite_and_accept_adds_player_to_team(make_player):
    captain = make_player("captain")
    recruit = make_player("recruit")
    team = team_services.create_team(creator=captain, name="Qarshi FC", city="Qarshi")

    invitation = team_services.invite_player(
        team=team, acting_user=captain.user, player_id=recruit.player_id
    )
    assert invitation.status == TeamInvitation.Status.PENDING

    team_services.respond_to_invitation(invitation=invitation, acting_user=recruit.user, accept=True)

    invitation.refresh_from_db()
    assert invitation.status == TeamInvitation.Status.ACCEPTED
    assert TeamMembership.objects.filter(team=team, player=recruit, is_active=True).exists()


def test_invite_and_reject_does_not_add_member(make_player):
    captain = make_player("captain")
    recruit = make_player("recruit")
    team = team_services.create_team(creator=captain, name="Qarshi FC", city="Qarshi")

    invitation = team_services.invite_player(
        team=team, acting_user=captain.user, player_id=recruit.player_id
    )
    team_services.respond_to_invitation(invitation=invitation, acting_user=recruit.user, accept=False)

    invitation.refresh_from_db()
    assert invitation.status == TeamInvitation.Status.REJECTED
    assert not TeamMembership.objects.filter(team=team, player=recruit, is_active=True).exists()


def test_only_captain_can_invite(make_player):
    captain = make_player("captain")
    bystander = make_player("bystander")
    recruit = make_player("recruit")
    team = team_services.create_team(creator=captain, name="Qarshi FC", city="Qarshi")

    with pytest.raises(PermissionDenied):
        team_services.invite_player(team=team, acting_user=bystander.user, player_id=recruit.player_id)


def test_cannot_invite_same_pending_player_twice(make_player):
    captain = make_player("captain")
    recruit = make_player("recruit")
    team = team_services.create_team(creator=captain, name="Qarshi FC", city="Qarshi")

    team_services.invite_player(team=team, acting_user=captain.user, player_id=recruit.player_id)
    with pytest.raises(ValidationError):
        team_services.invite_player(team=team, acting_user=captain.user, player_id=recruit.player_id)


def test_only_invited_player_can_respond(make_player):
    captain = make_player("captain")
    recruit = make_player("recruit")
    bystander = make_player("bystander")
    team = team_services.create_team(creator=captain, name="Qarshi FC", city="Qarshi")
    invitation = team_services.invite_player(
        team=team, acting_user=captain.user, player_id=recruit.player_id
    )

    with pytest.raises(PermissionDenied):
        team_services.respond_to_invitation(
            invitation=invitation, acting_user=bystander.user, accept=True
        )


def test_player_can_belong_to_multiple_teams(make_player):
    """Direct regression test for the spec requirement that a player is
    not rigidly bound to a single team."""
    captain_a = make_player("captain_a")
    captain_b = make_player("captain_b")
    recruit = make_player("recruit")

    team_a = team_services.create_team(creator=captain_a, name="Team A", city="Qarshi")
    team_b = team_services.create_team(creator=captain_b, name="Team B", city="Termez")

    inv_a = team_services.invite_player(team=team_a, acting_user=captain_a.user, player_id=recruit.player_id)
    inv_b = team_services.invite_player(team=team_b, acting_user=captain_b.user, player_id=recruit.player_id)
    team_services.respond_to_invitation(invitation=inv_a, acting_user=recruit.user, accept=True)
    team_services.respond_to_invitation(invitation=inv_b, acting_user=recruit.user, accept=True)

    assert TeamMembership.objects.filter(player=recruit, is_active=True).count() == 2
