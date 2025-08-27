from django.contrib import admin
from .models import Stock, Portfolio, Holding, Transaction, Watchlist, PortfolioReport, HoldingReport

admin.site.register(Stock)
# admin.site.register(Portfolio)
admin.site.register(Holding)
admin.site.register(Transaction)
admin.site.register(Watchlist)
admin.site.register(PortfolioReport)
admin.site.register(HoldingReport)
# trading/admin.py
from django.contrib import admin
from .models import Portfolio


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'visibility', 'cash_balance', 'total_value', 'created_at']
    list_filter = ['visibility', 'created_at', 'user']
    list_editable = ['visibility']  # Allows quick editing from the list view
    actions = ['make_public', 'make_private']

    def make_public(self, request, queryset):
        queryset.update(visibility='PUBLIC')

    make_public.short_description = "Make selected portfolios visible to users"

    def make_private(self, request, queryset):
        queryset.update(visibility='PRIVATE')

    make_private.short_description = "Hide selected portfolios from users"
