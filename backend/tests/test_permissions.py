import pytest

from teams import services as team_services
from tournaments.models import Tournament, TournamentAdmin

pytestmark = pytest.mark.django_db


def test_non_superuser_cannot_create_tournament(api_client, make_player):
    player = make_player("regular")
    api_client.force_authenticate(user=player.user)

    response = api_client.post(
        "/api/v1/tournaments/",
        {"name": "Rogue Cup", "city": "Qarshi", "groups_count": 1, "max_teams": 4},
        format="json",
    )
    assert response.status_code == 403


def test_superuser_can_create_tournament(api_client, make_superuser):
    admin = make_superuser()
    api_client.force_authenticate(user=admin)

    response = api_client.post(
        "/api/v1/tournaments/",
        {"name": "Official Cup", "city": "Qarshi", "groups_count": 1, "max_teams": 4},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["slug"] == "official-cup"


def test_tournament_admin_isolated_from_other_tournaments(api_client, make_player, make_superuser):
    admin = make_superuser()
    tournament_a = Tournament.objects.create(
        name="Cup A", city="Qarshi", created_by=admin, status=Tournament.Status.REGISTRATION_OPEN
    )
    tournament_b = Tournament.objects.create(
        name="Cup B", city="Qarshi", created_by=admin, status=Tournament.Status.REGISTRATION_OPEN
    )
    admin_of_b = make_player("admin_of_b").user
    TournamentAdmin.objects.create(tournament=tournament_b, user=admin_of_b, assigned_by=admin)

    api_client.force_authenticate(user=admin_of_b)

    # Allowed: this admin's own tournament.
    ok = api_client.get(f"/api/v1/tournaments/{tournament_b.slug}/registrations/")
    assert ok.status_code == 200

    # Forbidden: someone else's tournament.
    forbidden = api_client.get(f"/api/v1/tournaments/{tournament_a.slug}/registrations/")
    assert forbidden.status_code == 403

    forbidden_edit = api_client.patch(
        f"/api/v1/tournaments/{tournament_a.slug}/", {"description": "hijacked"}, format="json"
    )
    assert forbidden_edit.status_code == 403


def test_only_captain_can_invite_via_api(api_client, make_player):
    captain = make_player("captain")
    bystander = make_player("bystander")
    recruit = make_player("recruit")
    team = team_services.create_team(creator=captain, name="Qarshi FC", city="Qarshi")

    api_client.force_authenticate(user=bystander.user)
    response = api_client.post(
        f"/api/v1/teams/{team.slug}/invite/", {"player_id": recruit.player_id}, format="json"
    )
    assert response.status_code == 403


def test_player_cannot_edit_another_players_profile(api_client, make_player):
    player = make_player("player_one")
    other = make_player("player_two")

    api_client.force_authenticate(user=other.user)
    response = api_client.patch(
        f"/api/v1/players/{player.player_id.lstrip('#')}/", {"bio": "hijacked"}, format="json"
    )
    assert response.status_code == 403


def test_anonymous_can_read_public_endpoints(api_client, make_player):
    player = make_player("public_player")
    team = team_services.create_team(creator=player, name="Public FC", city="Qarshi")

    assert api_client.get("/api/v1/players/").status_code == 200
    assert api_client.get(f"/api/v1/teams/{team.slug}/").status_code == 200
    assert api_client.get("/api/v1/tournaments/").status_code == 200
