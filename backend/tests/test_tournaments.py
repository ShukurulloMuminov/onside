import pytest
from rest_framework.exceptions import PermissionDenied, ValidationError

from teams import services as team_services
from tournaments import services as tournament_services
from tournaments.models import Tournament, TournamentAdmin, TournamentRegistration

pytestmark = pytest.mark.django_db


def _make_tournament(created_by, **overrides):
    defaults = dict(
        name="Test Cup",
        city="Qarshi",
        format=Tournament.Format.GROUP_PLAYOFF,
        status=Tournament.Status.REGISTRATION_OPEN,
        groups_count=1,
        teams_per_group=4,
        qualifiers_per_group=2,
        max_teams=4,
        created_by=created_by,
    )
    defaults.update(overrides)
    return Tournament.objects.create(**defaults)


def test_apply_to_tournament_requires_captain(make_player, make_superuser):
    admin = make_superuser()
    captain = make_player("captain")
    bystander = make_player("bystander")
    team = team_services.create_team(creator=captain, name="Qarshi FC", city="Qarshi")
    tournament = _make_tournament(admin)

    with pytest.raises(PermissionDenied):
        tournament_services.apply_to_tournament(tournament=tournament, team=team, acting_user=bystander.user)


def test_apply_to_tournament_when_registration_closed_fails(make_player, make_superuser):
    admin = make_superuser()
    captain = make_player("captain")
    team = team_services.create_team(creator=captain, name="Qarshi FC", city="Qarshi")
    tournament = _make_tournament(admin, status=Tournament.Status.DRAFT)

    with pytest.raises(ValidationError):
        tournament_services.apply_to_tournament(tournament=tournament, team=team, acting_user=captain.user)


def test_review_registration_approves_and_rejects(make_player, make_superuser):
    admin = make_superuser()
    captain = make_player("captain")
    team = team_services.create_team(creator=captain, name="Qarshi FC", city="Qarshi")
    tournament = _make_tournament(admin)
    registration = tournament_services.apply_to_tournament(
        tournament=tournament, team=team, acting_user=captain.user
    )

    updated = tournament_services.review_registration(
        registration=registration, acting_user=admin, approve=True
    )
    assert updated.status == TournamentRegistration.Status.APPROVED

    with pytest.raises(ValidationError):
        # already reviewed
        tournament_services.review_registration(registration=updated, acting_user=admin, approve=False)


def test_tournament_admin_cannot_review_other_tournament(make_player, make_superuser):
    """Core object-level permission guarantee: a Tournament Admin only
    administers the tournaments they're explicitly assigned to."""
    admin = make_superuser()
    other_tournament_admin = make_player("other_admin").user
    captain = make_player("captain")
    team = team_services.create_team(creator=captain, name="Qarshi FC", city="Qarshi")

    tournament_a = _make_tournament(admin, name="Cup A")
    tournament_b = _make_tournament(admin, name="Cup B")
    TournamentAdmin.objects.create(tournament=tournament_b, user=other_tournament_admin, assigned_by=admin)

    registration = tournament_services.apply_to_tournament(
        tournament=tournament_a, team=team, acting_user=captain.user
    )

    with pytest.raises(PermissionDenied):
        tournament_services.review_registration(
            registration=registration, acting_user=other_tournament_admin, approve=True
        )


def test_generate_groups_requires_enough_approved_teams(make_player, make_superuser):
    admin = make_superuser()
    captain = make_player("captain")
    team = team_services.create_team(creator=captain, name="Qarshi FC", city="Qarshi")
    tournament = _make_tournament(admin, groups_count=1, teams_per_group=4)
    tournament_services.apply_to_tournament(tournament=tournament, team=team, acting_user=captain.user)

    with pytest.raises(ValidationError):
        tournament_services.generate_groups(tournament=tournament, acting_user=admin)
