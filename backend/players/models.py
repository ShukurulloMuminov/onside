from django.conf import settings
from django.db import models

from core.models import TimeStampedModel

PLAYER_ID_OFFSET = 1000


class PlayerProfile(TimeStampedModel):
    class Position(models.TextChoices):
        GOALKEEPER = "GK", "Goalkeeper"
        DEFENDER = "DF", "Defender"
        MIDFIELDER = "MF", "Midfielder"
        FORWARD = "FW", "Forward"

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="player_profile"
    )
    avatar = models.ImageField(upload_to="avatars/", null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)
    position = models.CharField(max_length=2, choices=Position.choices, blank=True)
    bio = models.TextField(blank=True)
    birth_date = models.DateField(null=True, blank=True)

    # --- Cached aggregate stats -------------------------------------
    # Single writer: stats.services.StatsService.recalculate_player().
    # Never set these directly anywhere else — see the plan's "stats are
    # a materialized cache, not hand input" rule. They exist purely so
    # profile/list views don't have to aggregate MatchEvent on every
    # request.
    matches_total = models.PositiveIntegerField(default=0)
    wins_total = models.PositiveIntegerField(default=0)
    goals_total = models.PositiveIntegerField(default=0)
    assists_total = models.PositiveIntegerField(default=0)
    mvp_total = models.PositiveIntegerField(default=0)
    yellow_cards_total = models.PositiveIntegerField(default=0)
    red_cards_total = models.PositiveIntegerField(default=0)
    tournaments_total = models.PositiveIntegerField(default=0)
    rating_avg = models.DecimalField(max_digits=4, decimal_places=2, default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.player_id} {self.user.get_full_name() or self.user.username}"

    @property
    def player_id(self) -> str:
        return f"#{PLAYER_ID_OFFSET + self.pk}"

    @staticmethod
    def pk_from_player_id(raw: str) -> int:
        """Reverses the player_id derivation. Accepts "#1024" or "1024"."""
        numeric = raw.lstrip("#")
        pk = int(numeric) - PLAYER_ID_OFFSET
        if pk <= 0:
            raise ValueError(f"Invalid player_id: {raw!r}")
        return pk
