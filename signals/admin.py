# signals/admin.py
from django.contrib import admin
from .models import TradeSignal

@admin.register(TradeSignal)
class TradeSignalAdmin(admin.ModelAdmin):
    list_display = ("created_at","symbol","trade_no","side","entry","main_sl","waiting","valid_until")
    list_filter  = ("symbol","side","waiting","valid_until")
    search_fields = ("symbol","trade_no","notes")
    ordering = ("-created_at",)