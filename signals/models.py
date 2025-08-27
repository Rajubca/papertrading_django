# signals/models.py
import uuid
from django.db import models

class TradeSignal(models.Model):
    class Side(models.TextChoices):
        BUY = "BUY", "Buy"
        SELL = "SELL", "Sell"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    symbol = models.CharField(max_length=40, db_index=True)   # e.g. Reliance, TCS
    trade_no = models.CharField(max_length=20, db_index=True) # e.g. TN11

    side = models.CharField(max_length=4, choices=Side.choices)
    entry = models.DecimalField(max_digits=12, decimal_places=2)

    main_sl = models.DecimalField("Main SL", max_digits=12, decimal_places=2)
    tp1 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tp2 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    tp3 = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)

    waiting = models.BooleanField(default=True)
    valid_until = models.DateField(null=True, blank=True)  # None => Today
    notes = models.TextField(blank=True)

    def as_message(self) -> str:
        # EXACT format you want
        parts = [
            f"{self.symbol} {self.trade_no} - {'Buy' if self.side=='BUY' else 'Sell'} {self.entry}",
            f"Main SL {self.main_sl}",
        ]
        if self.tp1: parts.append(f"TP1 {self.tp1}")
        if self.tp2: parts.append(f"TP2 {self.tp2}")
        if self.tp3: parts.append(f"TP3 {self.tp3}")
        parts.append(f"Waiting {'Yes' if self.waiting else 'No'}")
        valid = "Today" if not self.valid_until else self.valid_until.strftime("%d-%m-%Y")
        parts.append(f"Valid {valid}")
        if self.notes: parts.append(f"Notes: {self.notes}")
        return " | ".join(parts)

    class Meta:
        ordering = ("-created_at",)
