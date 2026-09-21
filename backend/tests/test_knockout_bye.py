import pytest
from rest_framework.exceptions import ValidationError

from matches.models import Match
from stats.services import KnockoutService
from teams import services as team_services
from tournaments.models import Tournament, TournamentRegistration

pytestmark = pytest.mark.django_db


def _make_tournament(created_by, **overrides):
    defaults = dict(
        name="Bye Test Cup",
        city="Qarshi",
        format=Tournament.Format.PLAYOFF,
        status=Tournament.Status.REGISTRATION_OPEN,
        created_by=created_by,
    )
    defaults.update(overrides)
    return Tournament.objects.create(**defaults)


def _register_approved_teams(tournament, admin, make_player, count):
    registrations = []
    for i in range(count):
        captain = make_player(f"byecap{i}")
        team = team_services.create_team(creator=captain, name=f"Bye Team {i}", city="Qarshi")
        reg = TournamentRegistration.objects.create(
            tournament=tournament, team=team, status=TournamentRegistration.Status.APPROVED
        )
        registrations.append(reg)
    return registrations


def test_six_qualifiers_get_an_eight_slot_bracket_with_two_byes(make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin)
    _register_approved_teams(tournament, admin, make_player, count=6)

    stage = KnockoutService.generate_bracket(tournament=tournament, acting_user=admin)

    round_names = list(stage.rounds.order_by("order").values_list("name", flat=True))
    assert round_names == ["quarterfinal", "semifinal", "final"]

    qf_matches = Match.objects.filter(knockout_round__stage=stage, knockout_round__name="quarterfinal")
    sf_matches = Match.objects.filter(knockout_round__stage=stage, knockout_round__name="semifinal")
    final_matches = Match.objects.filter(knockout_round__stage=stage, knockout_round__name="final")

    # 6 qualifiers -> 2 byes -> only 2 real quarterfinal matches (not 4).
    assert qf_matches.count() == 2
    assert sf_matches.count() == 2
    assert final_matches.count() == 1

    # Across the two semifinals, exactly 2 slots are already filled (the
    # bye'd teams) and 2 are still empty (waiting on quarterfinal winners).
    filled_slots = sum(
        (1 if m.home_registration_id else 0) + (1 if m.away_registration_id else 0) for m in sf_matches
    )
    assert filled_slots == 2

    # Every quarterfinal match feeds into one of the semifinals.
    for m in qf_matches:
        assert m.feeds_into_match_id in set(sf_matches.values_list("id", flat=True))


def test_byes_propagate_correctly_when_quarterfinals_are_played(make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin)
    _register_approved_teams(tournament, admin, make_player, count=6)
    KnockoutService.generate_bracket(tournament=tournament, acting_user=admin)

    qf_matches = list(Match.objects.filter(tournament=tournament, knockout_round__name="quarterfinal"))
    for m in qf_matches:
        m.status = Match.Status.FINISHED
        m.home_score, m.away_score = 2, 1
        m.save()

    sf_matches = Match.objects.filter(tournament=tournament, knockout_round__name="semifinal")
    for m in sf_matches:
        assert m.home_registration_id is not None
        assert m.away_registration_id is not None


def test_exact_power_of_two_still_works_with_no_byes(make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin)
    _register_approved_teams(tournament, admin, make_player, count=4)

    stage = KnockoutService.generate_bracket(tournament=tournament, acting_user=admin)

    # With n == target_size == 4, round order is [semifinal, final], and the
    # semifinal round IS round 1 — every slot is filled directly from the
    # qualifiers, with no byes and nothing left for advance() to fill in.
    sf_matches = Match.objects.filter(knockout_round__stage=stage, knockout_round__name="semifinal")
    assert sf_matches.count() == 2
    for m in sf_matches:
        assert m.home_registration_id is not None
        assert m.away_registration_id is not None


def test_rejects_fewer_than_two_qualifiers(make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin)
    _register_approved_teams(tournament, admin, make_player, count=1)

    with pytest.raises(ValidationError):
        KnockoutService.generate_bracket(tournament=tournament, acting_user=admin)


def test_rejects_more_than_sixteen_qualifiers(make_player, make_superuser):
    admin = make_superuser()
    tournament = _make_tournament(admin)
    _register_approved_teams(tournament, admin, make_player, count=17)

    with pytest.raises(ValidationError):
        KnockoutService.generate_bracket(tournament=tournament, acting_user=admin)
