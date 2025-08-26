from django.contrib import admin
from .models import Stock, Watchlist, Trade, Account, Portfolio

from django.contrib import admin


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ('trading_symbol', 'name', 'exchange', 'last_price', 'updated_at')
    search_fields = ('trading_symbol', 'name', 'isin', 'exchange')
    list_filter = ('exchange', 'instrument')


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'created_at')
    search_fields = ('user__username', 'name')


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ("user", "name", "virtual_balance", "total_pnl", "created_at")
    search_fields = ("user__username", "name")


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    list_display = ("portfolio", "stock", "trade_type", "quantity", "price", "timestamp")
    list_filter = ("trade_type", "portfolio")
    search_fields = ("portfolio__name", "stock__trading_symbol")


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'virtual_balance', 'total_pnl')
    search_fields = ('user__username',)
