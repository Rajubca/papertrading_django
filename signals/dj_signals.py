# signals/dj_signals.py
import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import TradeSignal
from .serializers import TradeSignalSerializer
from .utils import group_all, group_for_symbol
from .bus import safe_group_send

log = logging.getLogger("signals")

@receiver(post_save, sender=TradeSignal)
def on_trade_saved(sender, instance: TradeSignal, **kwargs):
    data = TradeSignalSerializer(instance).data
    try:
        safe_group_send(group_all(), data)
        safe_group_send(group_for_symbol(instance.symbol), data)
    except Exception:
        log.exception("Broadcast failed for trade %s", instance.pk)  # avoids Admin 500 if anything slips
