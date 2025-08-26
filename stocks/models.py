from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Stock(models.Model):
    trading_symbol = models.CharField(max_length=50, unique=True)  # tradingSymbol
    name = models.CharField(max_length=255, blank=True, null=True)  # name
    exchange = models.CharField(max_length=20, blank=True, null=True)  # NSE/BSE
    isin = models.CharField(max_length=20, blank=True, null=True)  # ISIN
    instrument = models.CharField(max_length=20, blank=True, null=True)  # EQ/FUTIDX/OPTSTK etc.
    last_price = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)  # lastPrice
    expiry = models.DateField(blank=True, null=True)  # For F&O contracts
    strike_price = models.DecimalField(max_digits=20, decimal_places=2, blank=True, null=True)
    option_type = models.CharField(max_length=10, blank=True, null=True)  # CE/PE
    lotsize = models.IntegerField(default=1)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["trading_symbol"]

    def __str__(self):
        return f"{self.trading_symbol} ({self.exchange}) - {self.name or ''}"


class Portfolio(models.Model):
    """Multiple portfolios per user"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="stocks_portfolios"
    )
    name = models.CharField(max_length=100, default="My Portfolio")
    virtual_balance = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("100000.00"))
    total_pnl = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "name")  # Prevent duplicate portfolio names per user

    def __str__(self):
        return f"{self.user.username} - {self.name}"


class Account(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='account')
    virtual_balance = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('100000.00'))
    total_pnl = models.DecimalField(max_digits=20, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"Account: {self.user} (Balance: {self.virtual_balance})"


class Watchlist(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stocks_watchlists')
    name = models.CharField(max_length=120, default='Default')
    stocks = models.ManyToManyField(Stock, blank=True, related_name='stocks_watchlists')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'name')

    def __str__(self):
        return f"{self.user} - {self.name}"


class Trade(models.Model):
    BUY = 'BUY'
    SELL = 'SELL'
    TRADE_TYPES = [(BUY, 'Buy'), (SELL, 'Sell')]

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="stocks_trades",null=True,blank=True)
    # user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='trades')
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE, related_name='stocks_trades')
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=20, decimal_places=2)
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPES)
    timestamp = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.user} {self.trade_type} {self.quantity}x {self.stock.symbol} @ {self.price} on {self.timestamp}"
