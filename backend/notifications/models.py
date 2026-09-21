from django.db import models

from core.models import TimeStampedModel


class Notification(TimeStampedModel):
    class Type(models.TextChoices):
        TEAM_INVITE = "team_invite", "Team Invite"
        REGISTRATION_APPROVED = "registration_approved", "Registration Approved"
        REGISTRATION_REJECTED = "registration_rejected", "Registration Rejected"
        TOURNAMENT_STARTED = "tournament_started", "Tournament Started"
        BADGE_EARNED = "badge_earned", "Badge Earned"
        LEVEL_UP = "level_up", "Level Up"
        MATCH_RESULT = "match_result", "Match Result"
        MATCH_DISPUTED = "match_disputed", "Match Disputed"

    recipient = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="notifications"
    )
    type = models.CharField(max_length=32, choices=Type.choices)
    message = models.CharField(max_length=255)
    # Relative frontend path, e.g. "/tournaments/some-cup" — kept as a
    # plain string rather than a generic FK since notifications point at a
    # handful of different models and a page, not always a single object.
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.get_type_display()} -> {self.recipient}"
