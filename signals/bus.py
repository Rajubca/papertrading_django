# signals/bus.py
import logging
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .utils import sanitize_group

log = logging.getLogger("signals")

def safe_group_send(group_name: str, payload: dict):
    group = sanitize_group(str(group_name))
    if not group:
        log.error("Refusing to send to empty group. Raw group_name=%r", group_name)
        return
    async_to_sync(get_channel_layer().group_send)(group, {"type": "notify", "data": payload})
    log.info("Sent to group=%s", group)
