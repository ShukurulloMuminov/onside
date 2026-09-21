from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from matches.models import Match, MatchEvent


@receiver(post_save, sender=MatchEvent)
def on_match_event_saved(sender, instance, **kwargs):
    from .services import StatsService

    StatsService.recalculate_match(instance.match)


@receiver(post_delete, sender=MatchEvent)
def on_match_event_deleted(sender, instance, **kwargs):
    from .services import StatsService

    StatsService.recalculate_match(instance.match)


@receiver(post_save, sender=Match)
def on_match_saved(sender, instance, **kwargs):
    from .services import KnockoutService, StatsService

    StatsService.recalculate_match(instance)
    KnockoutService.advance(instance)
