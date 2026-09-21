from django.db import models
from django.utils.text import slugify

from core.models import TimeStampedModel

from .formations import DEFAULT_SQUAD_SIZE, FORMATIONS_BY_SIZE, SQUAD_SIZES, formation_choices


class Team(TimeStampedModel):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=170, unique=True, blank=True)
    logo = models.ImageField(upload_to="team_logos/", null=True, blank=True)
    captain = models.ForeignKey(
        "players.PlayerProfile", on_delete=models.PROTECT, related_name="captained_teams"
    )
    city = models.CharField(max_length=100, blank=True)
    founded_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    # How many players per side this team plays (mini-football/5-a-side,
    # 7-a-side, or full 11) — determines which starting-lineup formations
    # are offered, since amateur football is often played smaller-sided.
    squad_size = models.PositiveSmallIntegerField(
        choices=[(s, f"{s}x{s}") for s in SQUAD_SIZES], default=DEFAULT_SQUAD_SIZE
    )

    # --- Cached aggregate stats, single writer: stats.services.StatsService ---
    matches_total = models.PositiveIntegerField(default=0)
    wins_total = models.PositiveIntegerField(default=0)
    draws_total = models.PositiveIntegerField(default=0)
    losses_total = models.PositiveIntegerField(default=0)
    goals_for_total = models.PositiveIntegerField(default=0)
    goals_against_total = models.PositiveIntegerField(default=0)
    tournaments_total = models.PositiveIntegerField(default=0)
    trophies_total = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            n = 1
            while Team.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f"{base}-{n}"
            self.slug = slug

        squad_size_changed = False
        if self.pk:
            previous = Team.objects.filter(pk=self.pk).values_list("squad_size", flat=True).first()
            squad_size_changed = previous is not None and previous != self.squad_size

        super().save(*args, **kwargs)

        if squad_size_changed:
            # A lineup set for the old squad size (e.g. an 11-a-side
            # formation) is meaningless once the team is reconfigured to
            # 5x5/7x7 — drop it rather than leave a mismatched formation
            # dangling, so every view (edit form, public pitch graphic)
            # only ever sees a lineup valid for the *current* squad_size.
            lineup = getattr(self, "lineup", None)
            if lineup and lineup.formation not in FORMATIONS_BY_SIZE.get(self.squad_size, {}):
                lineup.delete()


class TeamMembership(TimeStampedModel):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="memberships")
    player = models.ForeignKey(
        "players.PlayerProfile", on_delete=models.CASCADE, related_name="team_memberships"
    )
    is_active = models.BooleanField(default=True)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("team", "player")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.player} @ {self.team}"


class TeamInvitation(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        REJECTED = "rejected", "Rejected"
        CANCELLED = "cancelled", "Cancelled"

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name="invitations")
    invited_player = models.ForeignKey(
        "players.PlayerProfile", on_delete=models.CASCADE, related_name="team_invitations"
    )
    invited_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="+"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.team} -> {self.invited_player} ({self.status})"


class TeamLineup(TimeStampedModel):
    """The captain's default starting XI — one per team, shown on the
    team's public page. Slot x/y pitch coordinates are a frontend
    presentation concern (see frontend/src/lib/formations.ts); this model
    only tracks which named slot (e.g. "ST1") each player fills."""

    team = models.OneToOneField(Team, on_delete=models.CASCADE, related_name="lineup")
    formation = models.CharField(max_length=10, choices=formation_choices(), default="4-4-2")

    def __str__(self):
        return f"{self.team} lineup ({self.formation})"


class TeamLineupSlot(TimeStampedModel):
    lineup = models.ForeignKey(TeamLineup, on_delete=models.CASCADE, related_name="slots")
    code = models.CharField(max_length=10)
    player = models.ForeignKey(
        "players.PlayerProfile", on_delete=models.SET_NULL, null=True, blank=True, related_name="lineup_slots"
    )

    class Meta:
        unique_together = ("lineup", "code")
        ordering = ["code"]

    def __str__(self):
        return f"{self.lineup.team} {self.code} -> {self.player or 'boʼsh'}"
