from rest_framework import serializers
from .models import Stock, Portfolio, Holding, Transaction, Watchlist, PortfolioReport


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = '__all__'


class PortfolioSerializer(serializers.ModelSerializer):
    total_value = serializers.SerializerMethodField()

    class Meta:
        model = Portfolio
        fields = ['id', 'cash_balance', 'created_at', 'last_updated', 'total_value']

    def get_total_value(self, obj):
        return obj.total_value()


class HoldingSerializer(serializers.ModelSerializer):
    stock = StockSerializer()
    current_value = serializers.SerializerMethodField()
    profit_loss = serializers.SerializerMethodField()
    profit_loss_percentage = serializers.SerializerMethodField()

    class Meta:
        model = Holding
        fields = '__all__'

    def get_current_value(self, obj):
        return obj.current_value()

    def get_profit_loss(self, obj):
        return obj.profit_loss()

    def get_profit_loss_percentage(self, obj):
        return obj.profit_loss_percentage()


class TransactionSerializer(serializers.ModelSerializer):
    stock = StockSerializer()
    total_amount = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = '__all__'

    def get_total_amount(self, obj):
        return obj.total_amount()


class WatchlistSerializer(serializers.ModelSerializer):
    stocks = StockSerializer(many=True)

    class Meta:
        model = Watchlist
        fields = '__all__'


class PortfolioReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioReport
        fields = '__all__'