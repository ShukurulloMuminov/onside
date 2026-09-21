import pytest

from matches.models import Match
from stats.services import KnockoutService
from teams import services as team_services
from tournaments.models import Tournament, TournamentRegistration

pytestmark = pytest.mark.django_db


def _make_tournament(created_by, **overrides):
    defaults = dict(
        name="Third Place Cup",
        city="Qarshi",
        format=Tournament.Format.PLAYOFF,
        status=Tournament.Status.REGISTRATION_OPEN,
        created_by=created_by,
    )
    defaults.update(overrides)
    return Tournament.objects.create(**defaults)


def _register_approved_teams(tournament, make_player, count):
    registrations = []
    for i in range(count):
        captain = make_player(f"tpcap{i}")
        team = team_services.create_team(creator=captain, name=f"TP Team {i}", city="Qarshi")
        reg = TournamentRegistration.objects.create(
            tournament=tournament, team=team, status=TournamentRegistration.Status.APPROVED
        )
        registrations.append(reg)
    return registrations


def _finish(match, home_score, away_score):
    match.status = Match.Status.FINISHED
    match.home_score = home_score
    match.away_score = away_score
    match.save()


def test_third_place_match_created_once_both_semifinals_finish(make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin)
    _register_approved_teams(tournament, make_player, count=4)
    stage = KnockoutService.generate_bracket(tournament=tournament, acting_user=admin)

    sf_matches = list(Match.objects.filter(stage=stage, knockout_round__name="semifinal").order_by("id"))
    assert len(sf_matches) == 2

    # No third-place match/round should exist until the semifinals resolve.
    assert not Match.objects.filter(stage=stage, knockout_round__name="third_place").exists()

    _finish(sf_matches[0], 2, 1)
    third_place = Match.objects.filter(stage=stage, knockout_round__name="third_place").first()
    assert third_place is not None
    # Loser of the first semifinal (away team, 1 < 2) occupies the home slot.
    assert third_place.home_registration_id == sf_matches[0].away_registration_id
    assert third_place.away_registration_id is None

    _finish(sf_matches[1], 0, 3)
    third_place.refresh_from_db()
    # Loser of the second semifinal (home team, 0 < 3) occupies the away slot.
    assert third_place.away_registration_id == sf_matches[1].home_registration_id

    # Exactly one third-place match/round was created — not one per semifinal.
    assert Match.objects.filter(stage=stage, knockout_round__name="third_place").count() == 1


def test_third_place_survives_bye_bracket(make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin)
    _register_approved_teams(tournament, make_player, count=6)
    stage = KnockoutService.generate_bracket(tournament=tournament, acting_user=admin)

    qf_matches = list(Match.objects.filter(stage=stage, knockout_round__name="quarterfinal"))
    for m in qf_matches:
        _finish(m, 3, 0)

    sf_matches = list(Match.objects.filter(stage=stage, knockout_round__name="semifinal").order_by("id"))
    assert len(sf_matches) == 2
    for m in sf_matches:
        assert m.home_registration_id is not None
        assert m.away_registration_id is not None

    for m in sf_matches:
        _finish(m, 1, 4)

    third_place = Match.objects.get(stage=stage, knockout_round__name="third_place")
    assert third_place.home_registration_id is not None
    assert third_place.away_registration_id is not None


def test_no_third_place_round_for_two_qualifiers(make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin)
    _register_approved_teams(tournament, make_player, count=2)
    stage = KnockoutService.generate_bracket(tournament=tournament, acting_user=admin)

    final = Match.objects.get(stage=stage, knockout_round__name="final")
    _finish(final, 2, 0)

    assert not Match.objects.filter(stage=stage, knockout_round__name="third_place").exists()
