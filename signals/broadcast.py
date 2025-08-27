# signals/broadcast.py
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

def broadcast_trade(trade):
    from .serializers import TradeSignalSerializer
    layer = get_channel_layer()
    data = TradeSignalSerializer(trade).data
    async_to_sync(layer.group_send)("signals:all", {"type": "notify", "data": data})
    async_to_sync(layer.group_send)(f"signals:{trade.symbol}", {"type": "notify", "data": data})

# from asgiref.sync import async_to_sync
# from channels.layers import get_channel_layer
# from .utils import sanitize_group
# from .serializers import TradeSignalSerializer

# def broadcast_trade(trade):
#     layer = get_channel_layer()
#     payload = TradeSignalSerializer(trade).data
#     async_to_sync(layer.group_send)(sanitize_group("signals.all"), {"type": "notify", "data": payload})
#     async_to_sync(layer.group_send)(sanitize_group(f"signals.symbol.{trade.symbol}"),
#                                     {"type": "notify", "data": payload})
