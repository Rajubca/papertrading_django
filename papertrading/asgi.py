import os, django
from django.core.asgi import get_asgi_application
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from signals.routing import websocket_urlpatterns

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "papertrading.settings")
django.setup()

django_asgi_app = get_asgi_application()

application = ProtocolTypeRouter({
    # Serve static files (incl. admin CSS/JS) in dev over ASGI:
    "http": ASGIStaticFilesHandler(django_asgi_app),
    "websocket": AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
})
