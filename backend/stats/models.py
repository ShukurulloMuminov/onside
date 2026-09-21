from django.db import models

from core.models import TimeStampedModel


class PlayerMatchStats(TimeStampedModel):
    """Computed cache, one row per player who has at least one MatchEvent
    in a given match. Rebuilt in full by
    stats.services.StatsService.recalculate_match() every time that
    match's events change — never written to directly elsewhere."""

    match = models.ForeignKey(
        "matches.Match", on_delete=models.CASCADE, related_name="player_stats"
    )
    player = models.ForeignKey(
        "players.PlayerProfile", on_delete=models.CASCADE, related_name="match_stats"
    )
    team_registration = models.ForeignKey(
        "tournaments.TournamentRegistration",
        on_delete=models.CASCADE,
        related_name="player_match_stats",
    )
    goals = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)
    yellow_cards = models.PositiveIntegerField(default=0)
    red_cards = models.PositiveIntegerField(default=0)
    is_mvp = models.BooleanField(default=False)
    # Not populated in MVP1 (spec: match-performance rating is a later
    # enhancement) — reserved so it doesn't need a migration when it lands.
    rating = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True)

    class Meta:
        unique_together = ("match", "player")

    def __str__(self):
        return f"{self.player} in {self.match}"


class TeamMatchStats(TimeStampedModel):
    """Computed cache, one row per team per finished match. Derived
    strictly from Match.home_score/away_score (not from MatchEvent — see
    StatsService for why), rebuilt whenever the match result changes."""

    class Result(models.TextChoices):
        WIN = "win", "Win"
        DRAW = "draw", "Draw"
        LOSS = "loss", "Loss"

    match = models.ForeignKey("matches.Match", on_delete=models.CASCADE, related_name="team_stats")
    team_registration = models.ForeignKey(
        "tournaments.TournamentRegistration",
        on_delete=models.CASCADE,
        related_name="match_team_stats",
    )
    goals_for = models.PositiveIntegerField(default=0)
    goals_against = models.PositiveIntegerField(default=0)
    result = models.CharField(max_length=4, choices=Result.choices, null=True, blank=True)
    points = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ("match", "team_registration")

    def __str__(self):
        return f"{self.team_registration.team} in {self.match}"
