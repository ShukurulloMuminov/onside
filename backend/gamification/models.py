from django.db import models

from core.models import TimeStampedModel


class Level(TimeStampedModel):
    """Career progression tier (Rookie -> ... -> Legend). A player's
    current level is derived on read from their cached stats (see
    gamification.services.get_level_for_player) — not stored on
    PlayerProfile — so it can never drift out of sync with the stats it's
    based on. Super Admin can rename/re-tier these; that's the whole
    point of keeping them as editable rows instead of a hardcoded enum.
    """

    order = models.PositiveSmallIntegerField(unique=True)
    name = models.CharField(max_length=50)
    icon = models.CharField(max_length=10, blank=True)
    description = models.TextField(blank=True)
    required_points = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.order}. {self.name}"


class Badge(TimeStampedModel):
    """A badge definition (e.g. "Tournament Winner"). `is_automatic` is
    informational for now — MVP2 only supports Super Admin manually
    awarding badges via PlayerBadge; automatic criteria-based awarding
    is a later enhancement this field leaves room for."""

    name = models.CharField(max_length=100)
    icon = models.CharField(max_length=10, blank=True)
    description = models.TextField(blank=True)
    criteria = models.TextField(blank=True)
    is_automatic = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class PlayerBadge(TimeStampedModel):
    player = models.ForeignKey(
        "players.PlayerProfile", on_delete=models.CASCADE, related_name="badges"
    )
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name="awards")
    awarded_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="+"
    )

    class Meta:
        unique_together = ("player", "badge")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.player} — {self.badge}"
