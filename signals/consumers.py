from channels.generic.websocket import AsyncJsonWebsocketConsumer
from .utils import group_all, group_for_symbol

class FeedConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        self.g = group_all()
        await self.channel_layer.group_add(self.g, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.g, self.channel_name)

    async def notify(self, event):
        await self.send_json(event["data"])

class SymbolConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        symbol = self.scope["url_route"]["kwargs"]["symbol"]
        self.g = group_for_symbol(symbol)
        await self.channel_layer.group_add(self.g, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.g, self.channel_name)

    async def notify(self, event):
        await self.send_json(event["data"])
