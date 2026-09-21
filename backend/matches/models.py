from django.db import models

from core.models import TimeStampedModel


class Match(TimeStampedModel):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        LIVE = "live", "Live"
        FINISHED = "finished", "Finished"
        POSTPONED = "postponed", "Postponed"
        CANCELLED = "cancelled", "Cancelled"
        # Not driven by any workflow yet in MVP1 — reserved so the MVP2
        # match-confirmation feature (captains confirm the result) doesn't
        # need a schema migration when it lands.
        PENDING_CONFIRMATION = "pending_confirmation", "Pending Confirmation"

    class Slot(models.TextChoices):
        HOME = "home", "Home"
        AWAY = "away", "Away"

    tournament = models.ForeignKey(
        "tournaments.Tournament", on_delete=models.CASCADE, related_name="matches"
    )
    stage = models.ForeignKey(
        "tournaments.TournamentStage", on_delete=models.SET_NULL, null=True, blank=True, related_name="matches"
    )
    group = models.ForeignKey(
        "tournaments.Group", on_delete=models.SET_NULL, null=True, blank=True, related_name="matches"
    )
    knockout_round = models.ForeignKey(
        "tournaments.KnockoutRound",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="matches",
    )

    home_registration = models.ForeignKey(
        "tournaments.TournamentRegistration",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="home_matches",
    )
    away_registration = models.ForeignKey(
        "tournaments.TournamentRegistration",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="away_matches",
    )

    scheduled_date = models.DateField(null=True, blank=True)
    scheduled_time = models.TimeField(null=True, blank=True)
    venue = models.CharField(max_length=200, blank=True)
    referee = models.CharField(max_length=150, blank=True)

    status = models.CharField(max_length=25, choices=Status.choices, default=Status.SCHEDULED)
    home_score = models.PositiveIntegerField(null=True, blank=True)
    away_score = models.PositiveIntegerField(null=True, blank=True)
    penalty_home_score = models.PositiveIntegerField(null=True, blank=True)
    penalty_away_score = models.PositiveIntegerField(null=True, blank=True)

    # Knockout bracket auto-advance: once this match finishes, the winner
    # is placed into feeds_into_match's home/away slot by
    # stats.services.KnockoutService.advance(), triggered from a signal.
    feeds_into_match = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="fed_from"
    )
    feeds_into_slot = models.CharField(max_length=4, choices=Slot.choices, blank=True)

    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="+"
    )

    class Meta:
        ordering = ["scheduled_date", "scheduled_time"]

    def __str__(self):
        home = self.home_registration.team.name if self.home_registration else "TBD"
        away = self.away_registration.team.name if self.away_registration else "TBD"
        return f"{home} vs {away} ({self.tournament})"


class MatchConfirmation(TimeStampedModel):
    """One row per team once its captain confirms a submitted result.
    Match.status flips PENDING_CONFIRMATION -> FINISHED once both sides
    have confirmed (matches.services.confirm_result)."""

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="confirmations")
    team_registration = models.ForeignKey(
        "tournaments.TournamentRegistration", on_delete=models.CASCADE, related_name="match_confirmations"
    )
    confirmed_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="+"
    )

    class Meta:
        unique_together = ("match", "team_registration")

    def __str__(self):
        return f"{self.team_registration.team.name} confirmed {self.match_id}"


class MatchEvent(TimeStampedModel):
    class Type(models.TextChoices):
        GOAL = "goal", "Goal"
        ASSIST = "assist", "Assist"
        YELLOW_CARD = "yellow_card", "Yellow Card"
        RED_CARD = "red_card", "Red Card"
        OWN_GOAL = "own_goal", "Own Goal"
        SUBSTITUTION = "substitution", "Substitution"
        MVP = "mvp", "MVP"

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name="events")
    type = models.CharField(max_length=20, choices=Type.choices)
    player = models.ForeignKey(
        "players.PlayerProfile", on_delete=models.CASCADE, related_name="match_events"
    )
    team_registration = models.ForeignKey(
        "tournaments.TournamentRegistration", on_delete=models.CASCADE, related_name="match_events"
    )
    minute = models.PositiveSmallIntegerField(null=True, blank=True)
    related_event = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="related_events"
    )
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="+"
    )

    class Meta:
        ordering = ["minute", "created_at"]

    def __str__(self):
        return f"{self.get_type_display()} — {self.player} ({self.minute}')"
