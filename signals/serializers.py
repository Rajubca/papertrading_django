# signals/serializers.py
from rest_framework import serializers
from .models import TradeSignal

class TradeSignalSerializer(serializers.ModelSerializer):
    message = serializers.SerializerMethodField()
    class Meta:
        model = TradeSignal
        fields = ("id","created_at","symbol","trade_no","side","entry","main_sl",
                  "tp1","tp2","tp3","waiting","valid_until","notes","message")
    def get_message(self, obj): return obj.as_message()
