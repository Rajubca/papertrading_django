from django.urls import path
from . import views

app_name = 'stocks'

urlpatterns = [
    path('watchlist/', views.watchlist_view, name='watchlist'),
    path('stock/<str:symbol>/', views.stock_detail_view, name='detail'),
    path('watchlist/modify/', views.modify_watchlist, name='modify_watchlist'),
    path('trade/place/', views.place_trade_view, name='place_trade'),
    # path('portfolio/', views.portfolio_view, name='portfolio'),
    path('portfolios/', views.portfolio_list, name='portfolio'),
    path('portfolios/create/', views.portfolio_create, name='portfolio_create'),
    path('portfolios/<int:pk>/delete/', views.portfolio_delete, name='portfolio_delete'),

    path('orders/', views.orders_history_view, name='orders_history'),
]
