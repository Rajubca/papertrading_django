from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from trading import views as trading_views

urlpatterns = [
    # Admin URL
    path('admin/', admin.site.urls),
    
    # Authentication URLs (built-in Django auth)
    path('accounts/', include('django.contrib.auth.urls')),
    
    # Trading app URLs - this is where we mount our trading app
    path('trading/', include('trading.urls', namespace='trading')),
    
    # Redirect root URL to trading dashboard
    path('', RedirectView.as_view(url='/trading/', permanent=True)),


    path('accounts/signup/', trading_views.signup, name='signup'),  # Add this line
]

# Serve static files during development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)