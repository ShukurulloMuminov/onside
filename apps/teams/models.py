from django.db import models
from django.conf import settings


class Team(models.Model):
    """Jamoa modeli"""
    name = models.CharField(max_length=255, verbose_name='Jamoa nomi')
    short_name = models.CharField(max_length=10, blank=True, null=True, verbose_name='Qisqa nom (3-4 harf)')
    logo = models.ImageField(upload_to='team_logos/', blank=True, null=True)
    banner = models.ImageField(upload_to='team_banners/', blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    founded_year = models.PositiveIntegerField(blank=True, null=True)

    captain = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='captained_teams',
        verbose_name='Sardor'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Jamoa'
        verbose_name_plural = 'Jamoalar'
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def players_count(self):
        return self.memberships.filter(is_active=True).count()


class TeamMembership(models.Model):
    """Jamoa a'zoligi"""
    class Role(models.TextChoices):
        CAPTAIN = 'captain', 'Sardor'
        VICE_CAPTAIN = 'vice_captain', 'Sardor o\'rinbosari'
        PLAYER = 'player', 'O\'yinchi'

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships')
    player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='team_memberships'
    )
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PLAYER)
    jersey_number = models.PositiveIntegerField(blank=True, null=True, verbose_name='Futbolka raqami')
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Jamoa a\'zosi'
        verbose_name_plural = 'Jamoa a\'zolari'
        unique_together = ['team', 'player', 'is_active']

    def __str__(self):
        return f"{self.player.username} - {self.team.name}"


class TeamInvitation(models.Model):
    """Jamoaga taklif"""
    class Status(models.TextChoices):
        PENDING = 'pending', 'Kutilmoqda'
        ACCEPTED = 'accepted', 'Qabul qilindi'
        REJECTED = 'rejected', 'Rad etildi'
        CANCELLED = 'cancelled', 'Bekor qilindi'

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='invitations')
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations'
    )
    invited_player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_invitations'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'Taklif'
        verbose_name_plural = 'Takliflar'

    def __str__(self):
        return f"{self.team.name} -> {self.invited_player.username}"
