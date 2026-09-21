import functools
from collections import defaultdict

from django.conf import settings
from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Q, Sum
from django.db.models.functions import Coalesce
from rest_framework.exceptions import ValidationError

from matches.models import Match, MatchEvent

from .models import PlayerMatchStats, TeamMatchStats


# ---------------------------------------------------------------------------
# StatsService — the single writer for every cached stat counter in the
# system. Match/MatchEvent are the source of truth; everything else
# (PlayerProfile.*_total, Team.*_total, PlayerMatchStats, TeamMatchStats) is
# rebuilt from them here. Nothing outside this module should ever assign to
# those cached fields.
# ---------------------------------------------------------------------------
class StatsService:
    @staticmethod
    @transaction.atomic
    def recalculate_match(match: Match) -> None:
        affected_player_ids = StatsService._sync_player_match_stats(match)
        affected_team_ids = StatsService._sync_team_match_stats(match)
        for player_id in affected_player_ids:
            StatsService.recalculate_player_aggregate(player_id)
        for team_id in affected_team_ids:
            StatsService.recalculate_team_aggregate(team_id)

    @staticmethod
    def _sync_player_match_stats(match: Match) -> set[int]:
        # Deliberately queries MatchEvent directly by match_id rather than
        # match.events.all(): callers (e.g. MatchViewSet's queryset) may
        # pass in a `match` instance with a prefetch_related("events", ...)
        # cache already populated from *before* the event that triggered
        # this recalculation was created, which would silently serve stale
        # data instead of hitting the database.
        events = MatchEvent.objects.filter(match_id=match.pk)
        tallies: dict[int, dict] = defaultdict(
            lambda: {"goals": 0, "assists": 0, "yellow_cards": 0, "red_cards": 0, "is_mvp": False}
        )
        team_of_player: dict[int, int] = {}
        for event in events:
            t = tallies[event.player_id]
            team_of_player[event.player_id] = event.team_registration_id
            if event.type == MatchEvent.Type.GOAL:
                t["goals"] += 1
            elif event.type == MatchEvent.Type.ASSIST:
                t["assists"] += 1
            elif event.type == MatchEvent.Type.YELLOW_CARD:
                t["yellow_cards"] += 1
            elif event.type == MatchEvent.Type.RED_CARD:
                t["red_cards"] += 1
            elif event.type == MatchEvent.Type.MVP:
                t["is_mvp"] = True
            # OWN_GOAL / SUBSTITUTION don't add to the player's own tally.

        existing_ids = set(
            PlayerMatchStats.objects.filter(match=match).values_list("player_id", flat=True)
        )
        seen_ids = set(tallies.keys())

        for player_id, data in tallies.items():
            PlayerMatchStats.objects.update_or_create(
                match=match,
                player_id=player_id,
                defaults={"team_registration_id": team_of_player[player_id], **data},
            )
        stale_ids = existing_ids - seen_ids
        if stale_ids:
            PlayerMatchStats.objects.filter(match=match, player_id__in=stale_ids).delete()

        return existing_ids | seen_ids

    @staticmethod
    def _sync_team_match_stats(match: Match) -> set[int]:
        registrations = [r for r in (match.home_registration, match.away_registration) if r]
        team_ids = {r.team_id for r in registrations}

        is_decided = (
            match.status == Match.Status.FINISHED
            and match.home_score is not None
            and match.away_score is not None
            and match.home_registration_id
            and match.away_registration_id
        )
        if not is_decided:
            TeamMatchStats.objects.filter(match=match).delete()
            return team_ids

        tournament = match.tournament
        if match.home_score > match.away_score:
            home_result, away_result = TeamMatchStats.Result.WIN, TeamMatchStats.Result.LOSS
        elif match.home_score < match.away_score:
            home_result, away_result = TeamMatchStats.Result.LOSS, TeamMatchStats.Result.WIN
        else:
            home_result = away_result = TeamMatchStats.Result.DRAW

        points_by_result = {
            TeamMatchStats.Result.WIN: tournament.points_win,
            TeamMatchStats.Result.DRAW: tournament.points_draw,
            TeamMatchStats.Result.LOSS: tournament.points_loss,
        }

        TeamMatchStats.objects.update_or_create(
            match=match,
            team_registration=match.home_registration,
            defaults={
                "goals_for": match.home_score,
                "goals_against": match.away_score,
                "result": home_result,
                "points": points_by_result[home_result],
            },
        )
        TeamMatchStats.objects.update_or_create(
            match=match,
            team_registration=match.away_registration,
            defaults={
                "goals_for": match.away_score,
                "goals_against": match.home_score,
                "result": away_result,
                "points": points_by_result[away_result],
            },
        )
        return team_ids

    @staticmethod
    def recalculate_player_aggregate(player_id: int) -> None:
        from gamification.services import get_level_for_player
        from players.models import PlayerProfile

        player = PlayerProfile.objects.select_related("user").get(pk=player_id)
        old_level = get_level_for_player(player)

        stats_qs = PlayerMatchStats.objects.filter(player_id=player_id)
        agg = stats_qs.aggregate(
            goals=Coalesce(Sum("goals"), 0),
            assists=Coalesce(Sum("assists"), 0),
            yellow=Coalesce(Sum("yellow_cards"), 0),
            red=Coalesce(Sum("red_cards"), 0),
            mvp=Count("id", filter=Q(is_mvp=True)),
        )
        # "Matches played" and "tournaments played" are derived from having
        # at least one recorded event in a match — MVP1 has no separate
        # lineup/appearance model, so a player who plays a full match
        # without a goal/card/assist/MVP tag won't be counted here yet.
        matches_total = stats_qs.values("match_id").distinct().count()
        tournaments_total = stats_qs.values("match__tournament_id").distinct().count()
        wins_total = (
            stats_qs.annotate(
                is_win=Exists(
                    TeamMatchStats.objects.filter(
                        match_id=OuterRef("match_id"),
                        team_registration_id=OuterRef("team_registration_id"),
                        result=TeamMatchStats.Result.WIN,
                    )
                )
            )
            .filter(is_win=True)
            .values("match_id")
            .distinct()
            .count()
        )

        PlayerProfile.objects.filter(pk=player_id).update(
            matches_total=matches_total,
            wins_total=wins_total,
            goals_total=agg["goals"],
            assists_total=agg["assists"],
            mvp_total=agg["mvp"],
            yellow_cards_total=agg["yellow"],
            red_cards_total=agg["red"],
            tournaments_total=tournaments_total,
        )

        player.refresh_from_db()
        new_level = get_level_for_player(player)
        if new_level and (old_level is None or new_level.order > old_level.order):
            from notifications.models import Notification
            from notifications.services import notify

            notify(
                recipient=player.user,
                type=Notification.Type.LEVEL_UP,
                message=f'Tabriklaymiz! Siz "{new_level.name}" darajasiga chiqdingiz!',
                link=f"/players/{player.player_id}",
            )

    @staticmethod
    def recalculate_team_aggregate(team_id: int) -> None:
        from teams.models import Team

        tms_qs = TeamMatchStats.objects.filter(team_registration__team_id=team_id)
        agg = tms_qs.aggregate(
            matches=Count("id"),
            wins=Count("id", filter=Q(result=TeamMatchStats.Result.WIN)),
            draws=Count("id", filter=Q(result=TeamMatchStats.Result.DRAW)),
            losses=Count("id", filter=Q(result=TeamMatchStats.Result.LOSS)),
            goals_for=Coalesce(Sum("goals_for"), 0),
            goals_against=Coalesce(Sum("goals_against"), 0),
        )
        tournaments_total = tms_qs.values("match__tournament_id").distinct().count()

        Team.objects.filter(pk=team_id).update(
            matches_total=agg["matches"],
            wins_total=agg["wins"],
            draws_total=agg["draws"],
            losses_total=agg["losses"],
            goals_for_total=agg["goals_for"],
            goals_against_total=agg["goals_against"],
            tournaments_total=tournaments_total,
        )


# ---------------------------------------------------------------------------
# StandingsService — computed on every read from TeamMatchStats, never
# stored, so it can never disagree with the match data.
# ---------------------------------------------------------------------------
class StandingsService:
    @staticmethod
    def get_group_standings(group) -> list[dict]:
        tournament = group.stage.tournament
        tie_order = tournament.tie_breaker_config or list(settings.DEFAULT_TIE_BREAKER_ORDER)

        rows = []
        for gm in group.memberships.select_related("registration__team").all():
            reg = gm.registration
            tms = TeamMatchStats.objects.filter(team_registration=reg, match__group=group)
            agg = tms.aggregate(
                gf=Coalesce(Sum("goals_for"), 0),
                ga=Coalesce(Sum("goals_against"), 0),
                pts=Coalesce(Sum("points"), 0),
            )
            rows.append(
                {
                    "registration_id": reg.id,
                    "team": {"id": reg.team_id, "name": reg.team.name, "slug": reg.team.slug},
                    "played": tms.count(),
                    "won": tms.filter(result=TeamMatchStats.Result.WIN).count(),
                    "draw": tms.filter(result=TeamMatchStats.Result.DRAW).count(),
                    "lost": tms.filter(result=TeamMatchStats.Result.LOSS).count(),
                    "goals_for": agg["gf"],
                    "goals_against": agg["ga"],
                    "goal_difference": agg["gf"] - agg["ga"],
                    "points": agg["pts"],
                }
            )

        rows.sort(key=functools.cmp_to_key(lambda a, b: StandingsService._compare(a, b, tie_order, group)))
        for i, row in enumerate(rows):
            row["position"] = i + 1
            row["qualifies"] = i < tournament.qualifiers_per_group
        return rows

    @staticmethod
    def _compare(row_a, row_b, tie_order, group) -> int:
        field_map = {
            "points": "points",
            "goal_difference": "goal_difference",
            "goals_for": "goals_for",
        }
        for criterion in tie_order:
            if criterion == "head_to_head":
                result = StandingsService._head_to_head(row_a, row_b, group)
                if result != 0:
                    return result
                continue
            field = field_map.get(criterion)
            if not field or row_a[field] == row_b[field]:
                continue
            return row_b[field] - row_a[field]
        return 0

    @staticmethod
    def _head_to_head(row_a, row_b, group) -> int:
        """Simplified pairwise tiebreaker: points earned in matches directly
        between these two teams. NOTE: real football tie-break rules
        recompute a fresh mini-table for every group of 3+ teams tied
        together (iteratively); this pairwise version is a documented MVP1
        simplification and can mis-rank a genuine 3-way cycle."""
        ids = {row_a["team"]["id"], row_b["team"]["id"]}
        h2h = TeamMatchStats.objects.filter(
            match__group=group,
            match__home_registration__team_id__in=ids,
            match__away_registration__team_id__in=ids,
            team_registration__team_id__in=ids,
        )
        pts_a = sum(t.points for t in h2h if t.team_registration.team_id == row_a["team"]["id"])
        pts_b = sum(t.points for t in h2h if t.team_registration.team_id == row_b["team"]["id"])
        return pts_b - pts_a

    @staticmethod
    def get_tournament_standings(tournament) -> dict:
        from tournaments.models import TournamentStage

        stage = tournament.stages.filter(type=TournamentStage.Type.GROUP).order_by("-order").first()
        if not stage:
            return {"groups": []}
        return {
            "groups": [
                {"id": g.id, "name": g.name, "standings": StandingsService.get_group_standings(g)}
                for g in stage.groups.all()
            ]
        }


# ---------------------------------------------------------------------------
# KnockoutService — builds a single-elimination bracket from group-stage
# qualifiers (or straight from approved registrations for playoff-only
# tournaments) and auto-advances winners via Match.feeds_into_match.
# ---------------------------------------------------------------------------
ROUND_SEQUENCE_BY_SIZE = {
    16: ["round_of_16", "quarterfinal", "semifinal", "final"],
    8: ["quarterfinal", "semifinal", "final"],
    4: ["semifinal", "final"],
    2: ["final"],
}


class KnockoutService:
    @staticmethod
    def _seeding_order(n: int) -> list[int]:
        """Standard single-elimination seeding (1v8, 4v5, 2v7, 3v6 for
        n=8, ...) so top seeds are kept apart for as long as possible."""
        if n == 1:
            return [1]
        prev = KnockoutService._seeding_order(n // 2)
        order = []
        for s in prev:
            order.append(s)
            order.append(n + 1 - s)
        return order

    @staticmethod
    @transaction.atomic
    def generate_bracket(*, tournament, acting_user):
        from tournaments.services import require_tournament_admin

        require_tournament_admin(tournament, acting_user)

        from tournaments.models import KnockoutRound, Tournament, TournamentRegistration, TournamentStage

        if tournament.stages.filter(type=TournamentStage.Type.KNOCKOUT).exists():
            raise ValidationError("The knockout bracket has already been generated.")

        if tournament.format == Tournament.Format.GROUP_PLAYOFF:
            group_stage = tournament.stages.filter(type=TournamentStage.Type.GROUP).first()
            if not group_stage:
                raise ValidationError("Generate the group stage first.")
            qualifiers = []
            for group in group_stage.groups.order_by("name"):
                standings = StandingsService.get_group_standings(group)
                qualifiers.extend(row for row in standings if row["qualifies"])
        else:
            qualifiers = [
                {"registration_id": r.id}
                for r in tournament.registrations.filter(
                    status=TournamentRegistration.Status.APPROVED
                )
            ]

        n = len(qualifiers)
        if n < 2:
            raise ValidationError("Need at least 2 qualifying teams to generate a knockout bracket.")
        if n > 16:
            raise ValidationError(f"Knockout brackets support at most 16 qualifying teams; got {n}.")

        # Round sizing is based on the next power of two >= n, not n itself
        # — e.g. 6 qualifiers get an 8-slot bracket (quarterfinal onward)
        # with the top 2 seeds receiving a bye straight into round 2,
        # rather than requiring an exact 2/4/8/16 qualifier count.
        target_size = 1
        while target_size < n:
            target_size *= 2
        round_names = ROUND_SEQUENCE_BY_SIZE[target_size]

        stage = TournamentStage.objects.create(
            tournament=tournament, type=TournamentStage.Type.KNOCKOUT, name="Knockout Stage", order=1
        )
        rounds = [
            KnockoutRound.objects.create(stage=stage, name=name, order=i)
            for i, name in enumerate(round_names)
        ]

        # Only seeds 1..n have a real registration; seeds n+1..target_size
        # are byes. Standard seeding order always pairs each bye with one
        # of the top `target_size - n` seeds (never two byes together),
        # since a bracket is only ever short by less than half its slots.
        seed_to_registration_id = {i + 1: q["registration_id"] for i, q in enumerate(qualifiers)}
        order = KnockoutService._seeding_order(target_size)

        from matches.models import Match

        # Round 1: resolve byes immediately (no match created for that
        # pair — the bye'd team just occupies the round-2 slot directly).
        # Every entry is ("match", Match) or ("bye", registration_id).
        current_inputs: list[tuple[str, object]] = []
        for i in range(0, target_size, 2):
            reg_a = seed_to_registration_id.get(order[i])
            reg_b = seed_to_registration_id.get(order[i + 1])
            if reg_a and reg_b:
                m = Match.objects.create(
                    tournament=tournament,
                    stage=stage,
                    knockout_round=rounds[0],
                    home_registration_id=reg_a,
                    away_registration_id=reg_b,
                )
                current_inputs.append(("match", m))
            else:
                current_inputs.append(("bye", reg_a or reg_b))

        for round_obj in rounds[1:]:
            next_inputs: list[tuple[str, object]] = []
            for i in range(0, len(current_inputs), 2):
                kind_a, val_a = current_inputs[i]
                kind_b, val_b = current_inputs[i + 1]
                next_match = Match.objects.create(
                    tournament=tournament,
                    stage=stage,
                    knockout_round=round_obj,
                    home_registration_id=val_a if kind_a == "bye" else None,
                    away_registration_id=val_b if kind_b == "bye" else None,
                )
                if kind_a == "match":
                    val_a.feeds_into_match = next_match
                    val_a.feeds_into_slot = Match.Slot.HOME
                    val_a.save(update_fields=["feeds_into_match", "feeds_into_slot"])
                if kind_b == "match":
                    val_b.feeds_into_match = next_match
                    val_b.feeds_into_slot = Match.Slot.AWAY
                    val_b.save(update_fields=["feeds_into_match", "feeds_into_slot"])
                next_inputs.append(("match", next_match))
            current_inputs = next_inputs

        tournament.status = tournament.Status.IN_PROGRESS
        tournament.save(update_fields=["status", "updated_at"])

        # For GROUP_PLAYOFF tournaments, generate_groups() already sent the
        # "tournament started" notification when the group stage kicked
        # off — the knockout bracket here is a later phase of the same
        # tournament, not a second start.
        if tournament.format != Tournament.Format.GROUP_PLAYOFF:
            from notifications.models import Notification
            from notifications.services import notify_many

            captains = TournamentRegistration.objects.filter(
                id__in=[q["registration_id"] for q in qualifiers]
            ).select_related("team__captain__user")
            notify_many(
                recipients=[r.team.captain.user for r in captains if r.team.captain_id],
                type=Notification.Type.TOURNAMENT_STARTED,
                message=f'"{tournament.name}" turniri boshlandi!',
                link=f"/tournaments/{tournament.slug}",
            )
        return stage

    @staticmethod
    def advance(match) -> None:
        """Called after a knockout match is saved as finished. Resolves
        the winner and fills the next match's slot. Idempotent — safe to
        call on every save."""
        if not match.feeds_into_match_id:
            return
        if match.status != Match.Status.FINISHED:
            return
        if match.home_score is None or match.away_score is None:
            return

        if match.home_score > match.away_score:
            winner_id = match.home_registration_id
        elif match.away_score > match.home_score:
            winner_id = match.away_registration_id
        else:
            if match.penalty_home_score is None or match.penalty_away_score is None:
                return  # drawn in regulation, awaiting penalty entry
            winner_id = (
                match.home_registration_id
                if match.penalty_home_score > match.penalty_away_score
                else match.away_registration_id
            )

        field = "home_registration_id" if match.feeds_into_slot == Match.Slot.HOME else "away_registration_id"
        Match.objects.filter(pk=match.feeds_into_match_id).update(**{field: winner_id})

        loser_id = (
            match.away_registration_id if winner_id == match.home_registration_id else match.home_registration_id
        )
        if match.knockout_round_id and match.knockout_round.name == "semifinal":
            KnockoutService._advance_third_place(match, loser_id)

    @staticmethod
    def _advance_third_place(semifinal_match, loser_id) -> None:
        """Once a semifinal finishes, its loser is slotted into a 3rd-place
        match — created on first call, reused (get_or_create) on the
        second. Idempotent, so re-saving a finished semifinal is safe."""
        from tournaments.models import KnockoutRound

        stage = semifinal_match.stage
        round_obj, _ = KnockoutRound.objects.get_or_create(
            stage=stage, name=KnockoutRound.Name.THIRD_PLACE, defaults={"order": 99}
        )
        third_match, _ = Match.objects.get_or_create(
            tournament=semifinal_match.tournament, stage=stage, knockout_round=round_obj
        )

        semifinal_ids = list(
            Match.objects.filter(stage=stage, knockout_round_id=semifinal_match.knockout_round_id)
            .order_by("id")
            .values_list("id", flat=True)
        )
        field = "home_registration_id" if semifinal_ids[0] == semifinal_match.id else "away_registration_id"
        Match.objects.filter(pk=third_match.pk).update(**{field: loser_id})

    @staticmethod
    def get_bracket(tournament) -> dict:
        from tournaments.models import TournamentStage

        from matches.serializers import MatchSerializer

        stage = tournament.stages.filter(type=TournamentStage.Type.KNOCKOUT).order_by("-order").first()
        if not stage:
            return {"rounds": []}
        rounds = []
        for r in stage.rounds.all():
            matches = r.matches.select_related(
                "home_registration__team", "away_registration__team"
            ).all()
            rounds.append(
                {"name": r.name, "order": r.order, "matches": MatchSerializer(matches, many=True).data}
            )
        return {"rounds": rounds}


# ---------------------------------------------------------------------------
# RankingService — pluggable formula registry so the weighting can change
# without a migration (spec explicitly asks for this).
# ---------------------------------------------------------------------------
def _default_v1_formula(rows: list[dict]) -> list[dict]:
    for row in rows:
        row["score"] = row["goals"] * 4 + row["assists"] * 2 + row["wins"] * 1 + row["mvp"] * 3
    return sorted(rows, key=lambda r: r["score"], reverse=True)


RANKING_FORMULAS = {
    "default_v1": _default_v1_formula,
}


class RankingService:
    @staticmethod
    def get_player_rankings(*, scope: str = "global", tournament=None, formula_name: str | None = None, limit: int = 50):
        from players.serializers import PlayerProfileSerializer

        formula_name = formula_name or settings.DEFAULT_RANKING_FORMULA
        formula = RANKING_FORMULAS[formula_name]

        if scope == "tournament" and tournament is not None:
            rows = RankingService._tournament_scoped_rows(tournament)
        else:
            rows = RankingService._global_rows()

        ranked = formula(rows)[:limit]
        return [
            {
                "player": PlayerProfileSerializer(row["player"]).data,
                "score": row["score"],
                "goals": row["goals"],
                "assists": row["assists"],
                "wins": row["wins"],
                "mvp": row["mvp"],
                "matches": row["matches"],
            }
            for row in ranked
        ]

    @staticmethod
    def _global_rows() -> list[dict]:
        from players.models import PlayerProfile

        return [
            {
                "player": p,
                "goals": p.goals_total,
                "assists": p.assists_total,
                "wins": p.wins_total,
                "mvp": p.mvp_total,
                "matches": p.matches_total,
            }
            for p in PlayerProfile.objects.select_related("user").all()
        ]

    @staticmethod
    def _tournament_scoped_rows(tournament) -> list[dict]:
        from players.models import PlayerProfile

        pms = PlayerMatchStats.objects.filter(match__tournament=tournament).annotate(
            is_win=Exists(
                TeamMatchStats.objects.filter(
                    match_id=OuterRef("match_id"),
                    team_registration_id=OuterRef("team_registration_id"),
                    result=TeamMatchStats.Result.WIN,
                )
            )
        )
        agg_qs = pms.values("player_id").annotate(
            goals=Coalesce(Sum("goals"), 0),
            assists=Coalesce(Sum("assists"), 0),
            mvp=Count("id", filter=Q(is_mvp=True)),
            matches=Count("match_id", distinct=True),
            wins=Count("id", filter=Q(is_win=True)),
        )
        player_map = {
            p.id: p
            for p in PlayerProfile.objects.filter(
                pk__in=[r["player_id"] for r in agg_qs]
            ).select_related("user")
        }
        rows = []
        for r in agg_qs:
            player = player_map.get(r["player_id"])
            if not player:
                continue
            rows.append(
                {
                    "player": player,
                    "goals": r["goals"],
                    "assists": r["assists"],
                    "wins": r["wins"],
                    "mvp": r["mvp"],
                    "matches": r["matches"],
                }
            )
        return rows
