from django.db import models
from django.conf import settings


class Match(models.Model):
    """O'yin modeli"""
    class Status(models.TextChoices):
        SCHEDULED = 'scheduled', 'Rejalashtirilgan'
        LIVE = 'live', 'Jonli'
        FINISHED = 'finished', 'Tugallangan'
        POSTPONED = 'postponed', 'Kechiktirilgan'
        CANCELLED = 'cancelled', 'Bekor qilingan'

    class Stage(models.TextChoices):
        GROUP = 'group', 'Guruh bosqichi'
        ROUND_OF_16 = 'round_of_16', '1/8 final'
        QUARTER_FINAL = 'quarter_final', 'Chorak final'
        SEMI_FINAL = 'semi_final', 'Yarim final'
        THIRD_PLACE = 'third_place', 'Uchinchi o\'rin'
        FINAL = 'final', 'Final'
        LEAGUE = 'league', 'Liga'

    tournament = models.ForeignKey(
        'tournaments.Tournament',
        on_delete=models.CASCADE,
        related_name='matches'
    )
    group = models.ForeignKey(
        'tournaments.TournamentGroup',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='matches'
    )
    home_team = models.ForeignKey(
        'teams.Team',
        on_delete=models.CASCADE,
        related_name='home_matches'
    )
    away_team = models.ForeignKey(
        'teams.Team',
        on_delete=models.CASCADE,
        related_name='away_matches'
    )

    stage = models.CharField(max_length=20, choices=Stage.choices, default=Stage.LEAGUE)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED)

    match_date = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True, null=True)

    home_score = models.PositiveIntegerField(default=0)
    away_score = models.PositiveIntegerField(default=0)

    match_admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='administered_matches',
        help_text='Bu o\'yinda statistika kiritadigan admin'
    )

    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'O\'yin'
        verbose_name_plural = 'O\'yinlar'
        ordering = ['-match_date']

    def __str__(self):
        return f"{self.home_team.name} vs {self.away_team.name} | {self.match_date.date()}"

    @property
    def result(self):
        if self.status == 'finished':
            if self.home_score > self.away_score:
                return 'home_win'
            elif self.home_score < self.away_score:
                return 'away_win'
            return 'draw'
        return None


class MatchEvent(models.Model):
    """O'yin voqeasi: gol, assist, sariq/qizil karta"""
    class EventType(models.TextChoices):
        GOAL = 'goal', 'Gol'
        ASSIST = 'assist', 'Assist'
        YELLOW_CARD = 'yellow_card', 'Sariq karta'
        RED_CARD = 'red_card', 'Qizil karta'
        SUBSTITUTION_IN = 'substitution_in', 'Almashtirildi (kirdi)'
        SUBSTITUTION_OUT = 'substitution_out', 'Almashtirildi (chiqdi)'
        OWN_GOAL = 'own_goal', 'O\'z darvozasiga gol'

    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='events')
    player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='match_events'
    )
    team = models.ForeignKey(
        'teams.Team',
        on_delete=models.CASCADE,
        related_name='match_events'
    )
    event_type = models.CharField(max_length=20, choices=EventType.choices)
    minute = models.PositiveIntegerField(help_text='O\'yin daqiqasi')
    description = models.CharField(max_length=255, blank=True, null=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_events'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'O\'yin voqeasi'
        verbose_name_plural = 'O\'yin voqealari'
        ordering = ['minute']

    def __str__(self):
        return f"{self.get_event_type_display()} - {self.player.username} ({self.minute}')"


class PlayerMatchStat(models.Model):
    """O'yinchi bir o'yindagi statistikasi"""
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='player_stats')
    player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='player_stats'
    )
    team = models.ForeignKey(
        'teams.Team',
        on_delete=models.CASCADE,
        related_name='player_match_stats'
    )

    goals = models.PositiveIntegerField(default=0)
    assists = models.PositiveIntegerField(default=0)
    yellow_cards = models.PositiveIntegerField(default=0)
    red_cards = models.PositiveIntegerField(default=0)
    minutes_played = models.PositiveIntegerField(default=0)
    is_starting = models.BooleanField(default=True, help_text='Asosiy tarkibdami?')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'O\'yinchi statistikasi'
        verbose_name_plural = 'O\'yinchi statistikalari'
        unique_together = ['match', 'player']

    def __str__(self):
        return f"{self.player.username} | {self.match}"
