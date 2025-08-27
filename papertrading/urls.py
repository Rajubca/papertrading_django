from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from trading import views as trading_views

from rest_framework.routers import DefaultRouter
from signals.views import TradeSignalViewSet
# papertrading/urls.py
from django.urls import path, include
from django.contrib import admin
from rest_framework.routers import DefaultRouter
from signals.views import TradeSignalViewSet  # your API viewset from earlier
from signals.views_feed import SignalFeedPage


router = DefaultRouter()
router.register("signals", TradeSignalViewSet)

urlpatterns = [
    # path('', views.dashboard, name='dashboard'),  # <-- serves /trading/
    # Admin URL
    path('admin/', admin.site.urls),
    
    # Authentication URLs (built-in Django auth)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Trading app URLs - this is where we mount our trading app
    path('trading/', include('trading.urls', namespace='trading')),
    
    # Redirect root URL to trading dashboard
    path('', RedirectView.as_view(url='/trading/', permanent=True)),


    path('accounts/signup/', trading_views.signup, name='signup'),  # Add this line

    # API URLs for TradeSignal

    path("api/", include(router.urls)),
    path("app/signals/", SignalFeedPage.as_view(), name="signal_feed_all"),
    path("app/signals/<str:symbol>/", SignalFeedPage.as_view(), name="signal_feed_symbol"),
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)