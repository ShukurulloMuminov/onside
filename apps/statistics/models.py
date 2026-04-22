from django.db import models
from django.conf import settings


class PlayerTournamentStat(models.Model):
    """
    O'yinchining bir turnirdagi yig'ma statistikasi.
    Bu model har o'yin tugagandan so'ng yangilanadi.
    """
    player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tournament_stats'
    )
    tournament = models.ForeignKey(
        'tournaments.Tournament',
        on_delete=models.CASCADE,
        related_name='player_stats'
    )
    team = models.ForeignKey(
        'teams.Team',
        on_delete=models.CASCADE,
        related_name='tournament_player_stats'
    )

    matches_played = models.PositiveIntegerField(default=0)
    goals = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)
    yellow_cards = models.PositiveIntegerField(default=0)
    red_cards = models.PositiveIntegerField(default=0)
    minutes_played = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Turnir statistikasi'
        verbose_name_plural = 'Turnir statistikalari'
        unique_together = ['player', 'tournament']
        ordering = ['-goals', '-assists']

    def __str__(self):
        return f"{self.player.username} | {self.tournament.name}"


class TeamTournamentStat(models.Model):
    """Jamoaning bir turnirdagi yig'ma statistikasi"""
    team = models.ForeignKey(
        'teams.Team',
        on_delete=models.CASCADE,
        related_name='tournament_stats'
    )
    tournament = models.ForeignKey(
        'tournaments.Tournament',
        on_delete=models.CASCADE,
        related_name='team_stats'
    )

    matches_played = models.PositiveIntegerField(default=0)
    wins = models.PositiveIntegerField(default=0)
    draws = models.PositiveIntegerField(default=0)
    losses = models.PositiveIntegerField(default=0)
    goals_for = models.PositiveIntegerField(default=0)
    goals_against = models.PositiveIntegerField(default=0)
    points = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Jamoa statistikasi'
        verbose_name_plural = 'Jamoa statistikalari'
        unique_together = ['team', 'tournament']
        ordering = ['-points', '-goals_for']

    def __str__(self):
        return f"{self.team.name} | {self.tournament.name}"

    @property
    def goal_difference(self):
        return self.goals_for - self.goals_against
