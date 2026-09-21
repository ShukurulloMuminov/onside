from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Extends Django's built-in auth user rather than replacing it, so
    Django admin / is_staff / is_superuser keep working unmodified for the
    Super Admin role.

    Deliberately has no stored "role" field: Super Admin is
    `is_superuser`, and Tournament Admin is derived from membership in
    `tournaments.TournamentAdmin` (object-scoped, a user can admin some
    tournaments and not others). Storing a separate role flag here would
    just be a second place that fact could go stale in.
    """

    phone = models.CharField(max_length=20, unique=True, null=True, blank=True)
    city = models.CharField(max_length=100, blank=True)

    @property
    def is_tournament_admin(self) -> bool:
        return self.is_superuser or self.tournament_admin_roles.exists()

    def save(self, *args, **kwargs):
        # phone is unique but optional — an empty string (not NULL) is
        # what a blank form field produces, and a CharField unique
        # constraint treats every "" as a collision with every other "".
        # Normalize to NULL so only real duplicate numbers collide.
        if self.phone == "":
            self.phone = None
        super().save(*args, **kwargs)

    def __str__(self):
        return self.get_full_name() or self.username
