from django.db import models
from django.utils.text import slugify

from core.models import TimeStampedModel

DEFAULT_TIE_BREAKER_ORDER = ["points", "goal_difference", "goals_for", "head_to_head"]


class Tournament(TimeStampedModel):
    class Format(models.TextChoices):
        LEAGUE = "league", "League"
        GROUP_STAGE = "group_stage", "Group Stage"
        PLAYOFF = "playoff", "Playoff"
        GROUP_PLAYOFF = "group_playoff", "Group Stage + Playoff"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PENDING_APPROVAL = "pending_approval", "Pending Approval"
        PUBLISHED = "published", "Published"
        REGISTRATION_OPEN = "registration_open", "Registration Open"
        REGISTRATION_CLOSED = "registration_closed", "Registration Closed"
        IN_PROGRESS = "in_progress", "In Progress"
        FINISHED = "finished", "Finished"
        CANCELLED = "cancelled", "Cancelled"

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    banner = models.ImageField(upload_to="tournament_banners/", null=True, blank=True)
    description = models.TextField(blank=True)
    organizer = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=100, blank=True)
    venue = models.CharField(max_length=200, blank=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    format = models.CharField(max_length=20, choices=Format.choices, default=Format.GROUP_PLAYOFF)
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.DRAFT)
    max_teams = models.PositiveIntegerField(default=16)
    prize_info = models.TextField(blank=True)
    created_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="created_tournaments"
    )

    # Scoring / standings configuration — kept per-tournament rather than a
    # global constant so an admin can run a cup with different rules
    # without code changes.
    points_win = models.PositiveSmallIntegerField(default=3)
    points_draw = models.PositiveSmallIntegerField(default=1)
    points_loss = models.PositiveSmallIntegerField(default=0)
    tie_breaker_config = models.JSONField(default=list, blank=True)

    # Group-stage sizing, used by TournamentService.generate_groups().
    groups_count = models.PositiveIntegerField(default=0)
    teams_per_group = models.PositiveIntegerField(default=0)
    qualifiers_per_group = models.PositiveIntegerField(default=2)

    # When enabled, a result submitted by the tournament admin sits in
    # PENDING_CONFIRMATION until both team captains confirm it (or the
    # admin force-finalizes) — see matches.services.submit_result().
    require_match_confirmation = models.BooleanField(default=False)

    admins = models.ManyToManyField(
        "accounts.User",
        through="TournamentAdmin",
        through_fields=("tournament", "user"),
        related_name="administered_tournaments",
    )

    class Meta:
        ordering = ["-start_date", "-created_at"]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)
            slug = base
            n = 1
            while Tournament.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                n += 1
                slug = f"{base}-{n}"
            self.slug = slug
        if not self.tie_breaker_config:
            self.tie_breaker_config = list(DEFAULT_TIE_BREAKER_ORDER)
        super().save(*args, **kwargs)


class TournamentAdmin(TimeStampedModel):
    """Through-table for Tournament.admins. Object-scoped by design: a
    Tournament Admin only manages tournaments they appear in here, checked
    by core.permissions.IsTournamentAdminOfObject."""

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="admin_roles")
    user = models.ForeignKey(
        "accounts.User", on_delete=models.CASCADE, related_name="tournament_admin_roles"
    )
    assigned_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="+"
    )

    class Meta:
        unique_together = ("tournament", "user")

    def __str__(self):
        return f"{self.user} admins {self.tournament}"


class TournamentRegistration(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        WITHDRAWN = "withdrawn", "Withdrawn"

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="registrations")
    team = models.ForeignKey(
        "teams.Team", on_delete=models.CASCADE, related_name="tournament_registrations"
    )
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.PENDING)
    applied_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, related_name="+"
    )
    reviewed_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("tournament", "team")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.team} -> {self.tournament} ({self.status})"


class TournamentRosterPlayer(TimeStampedModel):
    registration = models.ForeignKey(
        TournamentRegistration, on_delete=models.CASCADE, related_name="roster"
    )
    player = models.ForeignKey(
        "players.PlayerProfile", on_delete=models.CASCADE, related_name="tournament_rosters"
    )
    jersey_number = models.PositiveSmallIntegerField(null=True, blank=True)
    is_captain = models.BooleanField(default=False)

    class Meta:
        unique_together = ("registration", "player")

    def __str__(self):
        return f"{self.player} ({self.registration.team})"


class TournamentStage(TimeStampedModel):
    class Type(models.TextChoices):
        GROUP = "group", "Group Stage"
        KNOCKOUT = "knockout", "Knockout"

    tournament = models.ForeignKey(Tournament, on_delete=models.CASCADE, related_name="stages")
    type = models.CharField(max_length=10, choices=Type.choices)
    name = models.CharField(max_length=100)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]

    def __str__(self):
        return f"{self.tournament} — {self.name}"


class Group(TimeStampedModel):
    stage = models.ForeignKey(TournamentStage, on_delete=models.CASCADE, related_name="groups")
    name = models.CharField(max_length=10)

    class Meta:
        ordering = ["name"]
        unique_together = ("stage", "name")

    def __str__(self):
        return f"{self.stage.tournament} — Group {self.name}"


class GroupMembership(TimeStampedModel):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="memberships")
    registration = models.ForeignKey(
        TournamentRegistration, on_delete=models.CASCADE, related_name="group_memberships"
    )

    class Meta:
        unique_together = ("group", "registration")

    def __str__(self):
        return f"{self.registration.team} in {self.group}"


class KnockoutRound(TimeStampedModel):
    class Name(models.TextChoices):
        ROUND_OF_16 = "round_of_16", "Round of 16"
        QUARTERFINAL = "quarterfinal", "Quarterfinal"
        SEMIFINAL = "semifinal", "Semifinal"
        FINAL = "final", "Final"
        THIRD_PLACE = "third_place", "Third Place"

    stage = models.ForeignKey(TournamentStage, on_delete=models.CASCADE, related_name="rounds")
    name = models.CharField(max_length=20, choices=Name.choices)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order"]
        unique_together = ("stage", "name")

    def __str__(self):
        return f"{self.stage.tournament} — {self.get_name_display()}"
