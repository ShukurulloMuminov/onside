from django.db import models
from django.conf import settings


class Tournament(models.Model):
    """Turnir modeli"""
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Tayyorlanmoqda'
        REGISTRATION = 'registration', 'Ro\'yxatga olish'
        ONGOING = 'ongoing', 'Davom etmoqda'
        FINISHED = 'finished', 'Tugallangan'
        CANCELLED = 'cancelled', 'Bekor qilingan'

    class Format(models.TextChoices):
        LEAGUE = 'league', 'Liga (barcha barchaga qarshi)'
        KNOCKOUT = 'knockout', 'Playoff (to\'g\'ridan-to\'g\'ri)'
        GROUP_KNOCKOUT = 'group_knockout', 'Guruh + Playoff'

    name = models.CharField(max_length=255, verbose_name='Turnir nomi')
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='tournaments/', blank=True, null=True)
    banner = models.ImageField(upload_to='tournament_banners/', blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_tournaments'
    )
    admins = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='administered_tournaments',
        blank=True,
        help_text='Turnirni boshqara oladigan adminlar'
    )

    format = models.CharField(max_length=20, choices=Format.choices, default=Format.LEAGUE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    max_teams = models.PositiveIntegerField(default=8)
    min_players_per_team = models.PositiveIntegerField(default=5)
    max_players_per_team = models.PositiveIntegerField(default=15)

    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)

    prize_info = models.TextField(blank=True, null=True, verbose_name='Sovrin haqida')
    rules = models.TextField(blank=True, null=True, verbose_name='Qoidalar')

    # Turnir hisobi: G'alaba, Durang, Mag'lubiyat uchun ball
    win_points = models.PositiveIntegerField(default=3)
    draw_points = models.PositiveIntegerField(default=1)
    loss_points = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Turnir'
        verbose_name_plural = 'Turnirlar'
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def is_admin(self, user):
        return user in self.admins.all() or user == self.created_by or user.role == 'superadmin'


class TournamentGroup(models.Model):
    """Guruh bosqichi uchun guruhlar"""
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='groups'
    )
    name = models.CharField(max_length=50, help_text='A guruh, B guruh va h.k.')

    class Meta:
        verbose_name = 'Guruh'
        verbose_name_plural = 'Guruhlar'
        unique_together = ['tournament', 'name']

    def __str__(self):
        return f"{self.tournament.name} - {self.name} guruh"


class TournamentRegistration(models.Model):
    """Jamoa turnirga ro'yxatga olish"""
    class Status(models.TextChoices):
        PENDING = 'pending', 'Kutilmoqda'
        APPROVED = 'approved', 'Tasdiqlangan'
        REJECTED = 'rejected', 'Rad etilgan'

    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='registrations'
    )
    team = models.ForeignKey(
        'teams.Team',
        on_delete=models.CASCADE,
        related_name='tournament_registrations'
    )
    group = models.ForeignKey(
        TournamentGroup,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teams'
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    registered_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    note = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Ro\'yxat'
        verbose_name_plural = 'Ro\'yxatlar'
        unique_together = ['tournament', 'team']

    def __str__(self):
        return f"{self.team.name} -> {self.tournament.name}"
