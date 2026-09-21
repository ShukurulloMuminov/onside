import pytest
from rest_framework.exceptions import PermissionDenied, ValidationError

from matches import services as match_services
from matches.models import Match, MatchConfirmation
from teams import services as team_services
from tournaments.models import Tournament, TournamentAdmin, TournamentRegistration

pytestmark = pytest.mark.django_db


def _make_tournament(created_by, **overrides):
    defaults = dict(
        name="Confirmation Cup",
        city="Qarshi",
        format=Tournament.Format.PLAYOFF,
        status=Tournament.Status.IN_PROGRESS,
        created_by=created_by,
    )
    defaults.update(overrides)
    return Tournament.objects.create(**defaults)


def _setup_match(make_player, tournament):
    home_captain = make_player("homecap")
    away_captain = make_player("awaycap")
    home_team = team_services.create_team(creator=home_captain, name="Home FC", city="Qarshi")
    away_team = team_services.create_team(creator=away_captain, name="Away FC", city="Qarshi")
    home_reg = TournamentRegistration.objects.create(
        tournament=tournament, team=home_team, status=TournamentRegistration.Status.APPROVED
    )
    away_reg = TournamentRegistration.objects.create(
        tournament=tournament, team=away_team, status=TournamentRegistration.Status.APPROVED
    )
    match = Match.objects.create(
        tournament=tournament, home_registration=home_reg, away_registration=away_reg
    )
    return match, home_captain, away_captain, home_reg, away_reg


def test_submit_result_finishes_immediately_when_confirmation_not_required(make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin, require_match_confirmation=False)
    match, *_ = _setup_match(make_player, tournament)
    TournamentAdmin.objects.create(tournament=tournament, user=admin, assigned_by=admin)

    match = match_services.submit_result(match=match, home_score=2, away_score=1, acting_user=admin)

    assert match.status == Match.Status.FINISHED
    assert match.home_score == 2 and match.away_score == 1


def test_either_captain_confirming_finishes_the_match(make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin, require_match_confirmation=True)
    match, home_captain, _away_captain, home_reg, _away_reg = _setup_match(make_player, tournament)
    TournamentAdmin.objects.create(tournament=tournament, user=admin, assigned_by=admin)

    match = match_services.submit_result(match=match, home_score=3, away_score=0, acting_user=admin)
    assert match.status == Match.Status.PENDING_CONFIRMATION

    # A single captain confirming is enough — waiting on both would stall
    # on whichever side has no reason to bother (usually the winner).
    match = match_services.confirm_result(match=match, acting_user=home_captain.user)
    assert match.status == Match.Status.FINISHED
    assert MatchConfirmation.objects.filter(match=match, team_registration=home_reg).exists()


def test_only_a_captain_of_either_team_can_confirm(make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin, require_match_confirmation=True)
    match, *_ = _setup_match(make_player, tournament)
    TournamentAdmin.objects.create(tournament=tournament, user=admin, assigned_by=admin)
    match_services.submit_result(match=match, home_score=1, away_score=1, acting_user=admin)

    bystander = make_player("bystander")
    with pytest.raises(PermissionDenied):
        match_services.confirm_result(match=match, acting_user=bystander.user)


def test_confirming_an_already_finished_match_is_rejected(make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin, require_match_confirmation=True)
    match, home_captain, away_captain, *_ = _setup_match(make_player, tournament)
    TournamentAdmin.objects.create(tournament=tournament, user=admin, assigned_by=admin)
    match_services.submit_result(match=match, home_score=1, away_score=0, acting_user=admin)
    match_services.confirm_result(match=match, acting_user=home_captain.user)

    with pytest.raises(ValidationError):
        match_services.confirm_result(match=match, acting_user=away_captain.user)


def test_dispute_reverts_to_scheduled_and_clears_score(make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin, require_match_confirmation=True)
    match, _home_captain, away_captain, *_ = _setup_match(make_player, tournament)
    TournamentAdmin.objects.create(tournament=tournament, user=admin, assigned_by=admin)
    match_services.submit_result(match=match, home_score=5, away_score=0, acting_user=admin)

    match = match_services.dispute_result(match=match, acting_user=away_captain.user)

    assert match.status == Match.Status.SCHEDULED
    assert match.home_score is None
    assert match.away_score is None
    assert match.confirmations.count() == 0


def test_dispute_requires_a_captain(make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin, require_match_confirmation=True)
    match, *_ = _setup_match(make_player, tournament)
    TournamentAdmin.objects.create(tournament=tournament, user=admin, assigned_by=admin)
    match_services.submit_result(match=match, home_score=1, away_score=0, acting_user=admin)

    bystander = make_player("bystander4")
    with pytest.raises(PermissionDenied):
        match_services.dispute_result(match=match, acting_user=bystander.user)


def test_dispute_only_works_while_pending_confirmation(make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin, require_match_confirmation=False)
    match, _home_captain, away_captain, *_ = _setup_match(make_player, tournament)
    TournamentAdmin.objects.create(tournament=tournament, user=admin, assigned_by=admin)
    match_services.submit_result(match=match, home_score=1, away_score=0, acting_user=admin)

    with pytest.raises(ValidationError):
        match_services.dispute_result(match=match, acting_user=away_captain.user)


def test_force_finalize_bypasses_pending_confirmation(make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin, require_match_confirmation=True)
    match, *_ = _setup_match(make_player, tournament)
    TournamentAdmin.objects.create(tournament=tournament, user=admin, assigned_by=admin)
    match_services.submit_result(match=match, home_score=4, away_score=2, acting_user=admin)

    # Neither captain has responded — admin closes it out anyway.
    match = match_services.force_finalize(match=match, acting_user=admin)

    assert match.status == Match.Status.FINISHED


def test_force_finalize_requires_tournament_admin(make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin, require_match_confirmation=True)
    match, *_ = _setup_match(make_player, tournament)
    TournamentAdmin.objects.create(tournament=tournament, user=admin, assigned_by=admin)
    match_services.submit_result(match=match, home_score=4, away_score=2, acting_user=admin)

    bystander = make_player("bystander2")
    with pytest.raises(PermissionDenied):
        match_services.force_finalize(match=match, acting_user=bystander.user)


def test_resubmitting_a_result_clears_prior_confirmations(make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin, require_match_confirmation=True)
    match, home_captain, *_ = _setup_match(make_player, tournament)
    TournamentAdmin.objects.create(tournament=tournament, user=admin, assigned_by=admin)
    match_services.submit_result(match=match, home_score=1, away_score=0, acting_user=admin)
    match_services.confirm_result(match=match, acting_user=home_captain.user)
    assert match.confirmations.count() == 1

    match = match_services.submit_result(match=match, home_score=2, away_score=2, acting_user=admin)

    assert match.confirmations.count() == 0
    assert match.status == Match.Status.PENDING_CONFIRMATION


def test_submit_result_requires_both_teams_set(make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin)
    TournamentAdmin.objects.create(tournament=tournament, user=admin, assigned_by=admin)
    match = Match.objects.create(tournament=tournament)

    with pytest.raises(ValidationError):
        match_services.submit_result(match=match, home_score=1, away_score=0, acting_user=admin)


def test_submit_result_requires_tournament_admin(make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin)
    match, *_ = _setup_match(make_player, tournament)
    TournamentAdmin.objects.create(tournament=tournament, user=admin, assigned_by=admin)

    bystander = make_player("bystander3")
    with pytest.raises(PermissionDenied):
        match_services.submit_result(match=match, home_score=1, away_score=0, acting_user=bystander.user)


def test_api_submit_and_confirm_flow(api_client, make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin, require_match_confirmation=True)
    match, home_captain, *_ = _setup_match(make_player, tournament)
    TournamentAdmin.objects.create(tournament=tournament, user=admin, assigned_by=admin)

    api_client.force_authenticate(user=admin)
    resp = api_client.post(
        f"/api/v1/matches/{match.id}/submit-result/", {"home_score": 2, "away_score": 0}, format="json"
    )
    assert resp.status_code == 200
    assert resp.data["status"] == "pending_confirmation"

    api_client.force_authenticate(user=home_captain.user)
    resp = api_client.post(f"/api/v1/matches/{match.id}/confirm/", format="json")
    assert resp.status_code == 200
    assert resp.data["status"] == "finished"


def test_api_dispute_flow(api_client, make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin, require_match_confirmation=True)
    match, _home_captain, away_captain, *_ = _setup_match(make_player, tournament)
    TournamentAdmin.objects.create(tournament=tournament, user=admin, assigned_by=admin)

    api_client.force_authenticate(user=admin)
    api_client.post(f"/api/v1/matches/{match.id}/submit-result/", {"home_score": 2, "away_score": 0}, format="json")

    api_client.force_authenticate(user=away_captain.user)
    resp = api_client.post(f"/api/v1/matches/{match.id}/dispute/", format="json")
    assert resp.status_code == 200
    assert resp.data["status"] == "scheduled"
    assert resp.data["home_score"] is None


def test_api_generic_patch_cannot_set_score(api_client, make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin)
    match, *_ = _setup_match(make_player, tournament)
    TournamentAdmin.objects.create(tournament=tournament, user=admin, assigned_by=admin)

    api_client.force_authenticate(user=admin)
    resp = api_client.patch(f"/api/v1/matches/{match.id}/", {"home_score": 9, "away_score": 9}, format="json")
    assert resp.status_code == 200
    match.refresh_from_db()
    assert match.home_score is None


def test_api_generic_patch_cannot_set_status_to_finished(api_client, make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin)
    match, *_ = _setup_match(make_player, tournament)
    TournamentAdmin.objects.create(tournament=tournament, user=admin, assigned_by=admin)

    api_client.force_authenticate(user=admin)
    resp = api_client.patch(f"/api/v1/matches/{match.id}/", {"status": "finished"}, format="json")
    assert resp.status_code == 400
    match.refresh_from_db()
    assert match.status == Match.Status.SCHEDULED


def test_api_generic_patch_can_still_set_other_statuses(api_client, make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin)
    match, *_ = _setup_match(make_player, tournament)
    TournamentAdmin.objects.create(tournament=tournament, user=admin, assigned_by=admin)

    api_client.force_authenticate(user=admin)
    resp = api_client.patch(f"/api/v1/matches/{match.id}/", {"status": "live"}, format="json")
    assert resp.status_code == 200
    match.refresh_from_db()
    assert match.status == Match.Status.LIVE
