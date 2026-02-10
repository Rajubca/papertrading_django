from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.db.models.signals import post_save
from django.dispatch import receiver

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=20, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=10000.00)

    def __str__(self):
        return f"{self.user.username}'s Profile"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

class Stock(models.Model):
    symbol = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    last_updated = models.DateTimeField(auto_now=True)

    sector = models.CharField(max_length=50, blank=True, null=True)
    industry = models.CharField(max_length=100, blank=True, null=True)
    exchange = models.CharField(max_length=50, blank=True, null=True)
    market_cap = models.DecimalField(max_digits=15, decimal_places=2, blank=True, null=True)
    day_high = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    day_low = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    year_high = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    year_low = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    @property
    def price_change(self):
        if self.day_high and self.day_low:
            return ((self.current_price - self.day_low) / self.day_low * 100).quantize(Decimal('0.01'))
        return Decimal('0.00')

    def __str__(self):
        return f"{self.symbol}"

class Portfolio(models.Model):
    VISIBILITY_CHOICES = (
        ('PUBLIC', 'Visible to Users'),
        ('PRIVATE', 'Hidden from Users'),
    )

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='portfolios')
    name = models.CharField(max_length=100, default='My Portfolio')
    initial_cash = models.DecimalField(max_digits=12, decimal_places=2, default=100000.00)
    invested_value = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    cash_balance = models.DecimalField(max_digits=15, decimal_places=2, default=100000.00)
    created_at = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_CHOICES,
        default='PUBLIC',
        help_text='Control whether this portfolio is visible to users'
    )
    @property
    def total_value(self):
        holdings = self.holdings.all()
        total = self.cash_balance
        for holding in holdings:
            total += holding.current_value
        return total

    @property
    def invested_value(self):
        # Correctly handles negative values (short positions) as liabilities effectively
        # But strictly speaking, invested value usually means Long positions.
        # For Short, it's liability.
        # But for total_value calculation: Cash + Sum(Holdings Value).
        # Short Holding Value = -Qty * Price (Negative).
        # So Total Value = Cash + (Negative Value) = Cash - Liability. Correct.
        return sum(h.current_value for h in self.holdings.all())

    def generate_report(self):
        """Generate a portfolio report snapshot"""
        from .models import PortfolioReport, HoldingReport

        # Calculate current values
        holdings = self.holdings.all()
        investment_value = sum(h.current_value for h in holdings)

        # Create the main report
        report = PortfolioReport.objects.create(
            portfolio=self,
            total_value=self.total_value,
            cash_balance=self.cash_balance,
            investment_value=investment_value
        )

        # Create holding snapshots for the report
        for holding in holdings:
            HoldingReport.objects.create(
                report=report,
                holding=holding,
                quantity=holding.quantity,
                current_price=holding.stock.current_price,
                average_price=holding.average_buy_price
            )

        return report

    def __str__(self):
        return f"{self.name} for {self.cash_balance}"

    def save(self, *args, **kwargs):
        if not self.pk and not self.initial_cash:
            self.initial_cash = self.cash_balance
        super().save(*args, **kwargs)

class Holding(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='holdings')
    stock = models.ForeignKey('Stock', on_delete=models.CASCADE)
    quantity = models.IntegerField()
    average_buy_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def current_value(self):
        return self.stock.current_price * Decimal(self.quantity)

    @property
    def profit_loss(self):
        return (self.stock.current_price - self.average_buy_price) * Decimal(self.quantity)

    @property
    def profit_loss_percentage(self):
        if self.average_buy_price == 0:
            return 0
        if self.quantity == 0:
            return 0

        pl_pct = ((self.stock.current_price - self.average_buy_price) / self.average_buy_price) * 100
        if self.quantity < 0:
             return -pl_pct
        return pl_pct

    class Meta:
        unique_together = ('portfolio', 'stock')

    def __str__(self):
        return f"{self.quantity} shares of {self.stock.symbol}"

class Transaction(models.Model):
    TRANSACTION_TYPES = (
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    )

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    stock = models.ForeignKey(Stock, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    quantity = models.IntegerField()
    price_per_share = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    @property
    def total_cost(self):
        return self.quantity * self.price_per_share

    def __str__(self):
        return f"{self.transaction_type} {self.quantity} of {self.stock.symbol} at {self.price_per_share}"

class PortfolioReport(models.Model):
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name='reports')
    report_date = models.DateField(auto_now_add=True)
    total_value = models.DecimalField(max_digits=15, decimal_places=2)
    cash_balance = models.DecimalField(max_digits=15, decimal_places=2)
    investment_value = models.DecimalField(max_digits=15, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-report_date']

    @property
    def profit_loss(self):
        previous_report = PortfolioReport.objects.filter(
            portfolio=self.portfolio,
            report_date__lt=self.report_date
        ).order_by('-report_date').first()

        if previous_report:
            return self.total_value - previous_report.total_value
        return Decimal('0.00')

    @property
    def profit_loss_percentage(self):
        previous_report = PortfolioReport.objects.filter(
            portfolio=self.portfolio,
            report_date__lt=self.report_date
        ).order_by('-report_date').first()

        if previous_report and previous_report.total_value > 0:
            return ((self.total_value - previous_report.total_value) / previous_report.total_value) * 100
        return Decimal('0.00')

    def __str__(self):
        return f"Report for {self.portfolio.user.username} on {self.report_date}"

class HoldingReport(models.Model):
    report = models.ForeignKey(PortfolioReport, on_delete=models.CASCADE, related_name='holding_reports')
    holding = models.ForeignKey(Holding, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    current_price = models.DecimalField(max_digits=10, decimal_places=2)
    average_price = models.DecimalField(max_digits=10, decimal_places=2)

    @property
    def current_value(self):
        return self.current_price * Decimal(self.quantity)

    @property
    def profit_loss(self):
        return (self.current_price - self.average_price) * Decimal(self.quantity)

    @property
    def profit_loss_percentage(self):
        if self.average_price == 0:
            return 0
        if self.quantity == 0:
            return 0

        pl_pct = ((self.current_price - self.average_price) / self.average_price) * 100
        if self.quantity < 0:
             return -pl_pct
        return pl_pct

    def __str__(self):
        return f"{self.holding.stock.symbol} in {self.report}"

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='watchlists')
    name = models.CharField(max_length=100)
    stocks = models.ManyToManyField(Stock, related_name='watchlists')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s {self.name} Watchlist"

class NSEData(models.Model):
    symbol = models.CharField(max_length=20)
    name = models.CharField(max_length=100)
    open_price = models.DecimalField(max_digits=10, decimal_places=2)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField()
    downloaded_at = models.DateTimeField(auto_now_add=True)
    index_type = models.CharField(max_length=20, choices=[('NIFTY50', 'Nifty 50'), ('FNO', 'F&O')])

    class Meta:
        indexes = [
            models.Index(fields=['symbol']),
            models.Index(fields=['index_type']),
        ]
