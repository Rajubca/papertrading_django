from django.urls import re_path
from .consumers import FeedConsumer, SymbolConsumer

websocket_urlpatterns = [
    re_path(r"ws/signals/$", FeedConsumer.as_asgi()),
    re_path(r"ws/signals/(?P<symbol>[A-Za-z0-9\-]+)/$", SymbolConsumer.as_asgi()),
]
