from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Onside UZ asosiy foydalanuvchi modeli.
    Uchta rol: SUPERADMIN, TOURNAMENT_ADMIN, PLAYER
    """
    class Role(models.TextChoices):
        SUPERADMIN = 'superadmin', 'Super Admin'
        TOURNAMENT_ADMIN = 'tournament_admin', 'Turnir Admin'
        PLAYER = 'player', 'O\'yinchi'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.PLAYER,
    )
    phone = models.CharField(max_length=13, blank=True, null=True, unique=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    position = models.CharField(
        max_length=20,
        choices=[
            ('goalkeeper', 'Darvozabon'),
            ('defender', 'Himoyachi'),
            ('midfielder', 'O\'rta yarim himoyachi'),
            ('forward', 'Hujumchi'),
        ],
        blank=True,
        null=True
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Foydalanuvchi'
        verbose_name_plural = 'Foydalanuvchilar'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

    @property
    def is_tournament_admin(self):
        return self.role in [self.Role.TOURNAMENT_ADMIN, self.Role.SUPERADMIN]

    @property
    def is_superadmin(self):
        return self.role == self.Role.SUPERADMIN
