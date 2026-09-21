import pytest

from matches.models import Match, MatchEvent
from stats.models import PlayerMatchStats, TeamMatchStats
from stats.services import KnockoutService, StandingsService
from teams import services as team_services
from teams.models import Team
from tournaments.models import (
    Group,
    GroupMembership,
    KnockoutRound,
    Tournament,
    TournamentRegistration,
    TournamentStage,
)

pytestmark = pytest.mark.django_db


def _make_tournament(created_by, **overrides):
    defaults = dict(
        name="Test Cup",
        city="Qarshi",
        status=Tournament.Status.IN_PROGRESS,
        groups_count=1,
        qualifiers_per_group=2,
        created_by=created_by,
    )
    defaults.update(overrides)
    return Tournament.objects.create(**defaults)


def _register(tournament, team):
    return TournamentRegistration.objects.create(
        tournament=tournament, team=team, status=TournamentRegistration.Status.APPROVED
    )


def _finish(match: Match, home_score: int, away_score: int):
    match.status = Match.Status.FINISHED
    match.home_score = home_score
    match.away_score = away_score
    match.save()
    match.refresh_from_db()
    return match


def test_recalculate_match_updates_player_and_team_aggregates(make_player, make_superuser):
    admin = make_superuser()
    scorer_captain = make_player("scorer_captain")
    assist_captain = make_player("assist_captain")
    team_a = team_services.create_team(creator=scorer_captain, name="Team A", city="Qarshi")
    team_b = team_services.create_team(creator=assist_captain, name="Team B", city="Termez")
    tournament = _make_tournament(admin)
    reg_a, reg_b = _register(tournament, team_a), _register(tournament, team_b)

    match = Match.objects.create(
        tournament=tournament, home_registration=reg_a, away_registration=reg_b
    )
    goal = MatchEvent.objects.create(
        match=match, type=MatchEvent.Type.GOAL, player=scorer_captain, team_registration=reg_a, minute=10
    )
    MatchEvent.objects.create(
        match=match,
        type=MatchEvent.Type.ASSIST,
        player=assist_captain,
        team_registration=reg_a,
        minute=10,
        related_event=goal,
    )

    scorer_captain.refresh_from_db()
    assist_captain.refresh_from_db()
    assert scorer_captain.goals_total == 1
    assert assist_captain.assists_total == 1

    _finish(match, 1, 0)
    team_a.refresh_from_db()
    scorer_captain.refresh_from_db()
    assert team_a.wins_total == 1
    assert scorer_captain.wins_total == 1

    # Reverting the match to not-finished must clear the derived team result
    # (TeamMatchStats is a cache, not an independent fact).
    match.status = Match.Status.SCHEDULED
    match.save()
    assert not TeamMatchStats.objects.filter(match=match).exists()
    team_a.refresh_from_db()
    assert team_a.wins_total == 0


def test_recalculate_match_removes_stale_player_stats_on_event_delete(make_player, make_superuser):
    admin = make_superuser()
    captain = make_player("captain")
    opp_captain = make_player("opp_captain")
    team_a = team_services.create_team(creator=captain, name="Team A", city="Qarshi")
    team_b = team_services.create_team(creator=opp_captain, name="Team B", city="Termez")
    tournament = _make_tournament(admin)
    reg_a, reg_b = _register(tournament, team_a), _register(tournament, team_b)
    match = Match.objects.create(tournament=tournament, home_registration=reg_a, away_registration=reg_b)

    event = MatchEvent.objects.create(
        match=match, type=MatchEvent.Type.GOAL, player=captain, team_registration=reg_a, minute=10
    )
    assert PlayerMatchStats.objects.filter(match=match, player=captain).exists()

    event.delete()
    assert not PlayerMatchStats.objects.filter(match=match, player=captain).exists()
    captain.refresh_from_db()
    assert captain.goals_total == 0


def test_group_standings_sorted_by_points_then_goal_difference(make_player, make_superuser):
    admin = make_superuser()
    captains = [make_player(f"cap{i}") for i in range(4)]
    teams = [
        team_services.create_team(creator=c, name=f"Team {i}", city="Qarshi")
        for i, c in enumerate(captains)
    ]
    tournament = _make_tournament(admin)
    stage = TournamentStage.objects.create(
        tournament=tournament, type=TournamentStage.Type.GROUP, name="Group Stage"
    )
    group = Group.objects.create(stage=stage, name="A")
    regs = [_register(tournament, t) for t in teams]
    for reg in regs:
        GroupMembership.objects.create(group=group, registration=reg)

    # Team 0 beats Team 1 big; Team 2 beats Team 3 narrowly; Team 0 and
    # Team 2 end up level on points, separated by goal difference.
    m1 = Match.objects.create(tournament=tournament, group=group, home_registration=regs[0], away_registration=regs[1])
    _finish(m1, 4, 0)
    m2 = Match.objects.create(tournament=tournament, group=group, home_registration=regs[2], away_registration=regs[3])
    _finish(m2, 1, 0)

    standings = StandingsService.get_group_standings(group)
    # Team 0 and Team 2 both have 3 points (one win each) — Team 0 ranks
    # above Team 2 on goal difference (+4 vs +1).
    assert standings[0]["team"]["id"] == teams[0].id
    assert standings[0]["points"] == 3
    assert standings[0]["goal_difference"] == 4
    assert standings[1]["team"]["id"] == teams[2].id
    assert standings[1]["goal_difference"] == 1
    # Team 3 and Team 1 both have 0 points (one loss each) — Team 3 ranks
    # above Team 1 on goal difference (-1 vs -4).
    assert standings[2]["team"]["id"] == teams[3].id
    assert standings[2]["goal_difference"] == -1
    assert standings[3]["team"]["id"] == teams[1].id
    assert standings[3]["goal_difference"] == -4


def test_knockout_advance_fills_next_round_slot(make_player, make_superuser):
    admin = make_superuser()
    captains = [make_player(f"kocap{i}") for i in range(4)]
    teams = [
        team_services.create_team(creator=c, name=f"KO Team {i}", city="Qarshi")
        for i, c in enumerate(captains)
    ]
    tournament = _make_tournament(admin, format=Tournament.Format.PLAYOFF)
    regs = [_register(tournament, t) for t in teams]

    stage = TournamentStage.objects.create(
        tournament=tournament, type=TournamentStage.Type.KNOCKOUT, name="Knockout"
    )
    semi = KnockoutRound.objects.create(stage=stage, name=KnockoutRound.Name.SEMIFINAL, order=0)
    final_round = KnockoutRound.objects.create(stage=stage, name=KnockoutRound.Name.FINAL, order=1)

    final_match = Match.objects.create(tournament=tournament, stage=stage, knockout_round=final_round)
    semi1 = Match.objects.create(
        tournament=tournament,
        stage=stage,
        knockout_round=semi,
        home_registration=regs[0],
        away_registration=regs[1],
        feeds_into_match=final_match,
        feeds_into_slot=Match.Slot.HOME,
    )
    semi2 = Match.objects.create(
        tournament=tournament,
        stage=stage,
        knockout_round=semi,
        home_registration=regs[2],
        away_registration=regs[3],
        feeds_into_match=final_match,
        feeds_into_slot=Match.Slot.AWAY,
    )

    _finish(semi1, 2, 1)  # regs[0] wins
    _finish(semi2, 0, 3)  # regs[3] wins

    final_match.refresh_from_db()
    assert final_match.home_registration_id == regs[0].id
    assert final_match.away_registration_id == regs[3].id


def test_knockout_advance_waits_for_penalties_on_draw(make_player, make_superuser):
    admin = make_superuser()
    captains = [make_player(f"pkcap{i}") for i in range(2)]
    teams = [
        team_services.create_team(creator=c, name=f"PK Team {i}", city="Qarshi")
        for i, c in enumerate(captains)
    ]
    tournament = _make_tournament(admin, format=Tournament.Format.PLAYOFF)
    regs = [_register(tournament, t) for t in teams]
    stage = TournamentStage.objects.create(
        tournament=tournament, type=TournamentStage.Type.KNOCKOUT, name="Knockout"
    )
    final_round = KnockoutRound.objects.create(stage=stage, name=KnockoutRound.Name.FINAL, order=0)
    next_match = Match.objects.create(tournament=tournament, stage=stage)
    match = Match.objects.create(
        tournament=tournament,
        stage=stage,
        knockout_round=final_round,
        home_registration=regs[0],
        away_registration=regs[1],
        feeds_into_match=next_match,
        feeds_into_slot=Match.Slot.HOME,
    )

    _finish(match, 1, 1)
    next_match.refresh_from_db()
    assert next_match.home_registration_id is None  # no penalties entered yet

    match.penalty_home_score = 5
    match.penalty_away_score = 4
    match.save()

    next_match.refresh_from_db()
    assert next_match.home_registration_id == regs[0].id
