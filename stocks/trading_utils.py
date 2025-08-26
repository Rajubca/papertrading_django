from decimal import Decimal
from .models import Trade
from collections import defaultdict


def _build_remaining_buy_lots(trades):
    buy_lots = []
    for t in trades:
        if t.trade_type == Trade.BUY:
            buy_lots.append({'qty': int(t.quantity), 'price': Decimal(t.price)})
        else:
            qty_to_sell = int(t.quantity)
            while qty_to_sell > 0 and buy_lots:
                lot = buy_lots[0]
                if lot['qty'] > qty_to_sell:
                    lot['qty'] -= qty_to_sell
                    qty_to_sell = 0
                else:
                    qty_to_sell -= lot['qty']
                    buy_lots.pop(0)
    return buy_lots


def available_quantity_for_user_stock(user, stock):
    trades = list(Trade.objects.filter(user=user, stock=stock).order_by('timestamp'))
    lots = _build_remaining_buy_lots(trades)
    return sum(l['qty'] for l in lots)


def compute_realized_pnl_for_sell(user, stock, sell_qty, sell_price):
    trades = list(Trade.objects.filter(user=user, stock=stock).order_by('timestamp'))
    lots = _build_remaining_buy_lots(trades)
    total_available = sum(l['qty'] for l in lots)
    if sell_qty > total_available:
        raise ValueError('Not enough shares to sell')
    qty_to_sell = sell_qty
    realized_pnl = Decimal('0.00')
    consumed = []
    for lot in lots:
        if qty_to_sell == 0:
            break
        take = min(lot['qty'], qty_to_sell)
        buy_price = Decimal(lot['price'])
        pnl = (Decimal(sell_price) - buy_price) * take
        realized_pnl += pnl
        consumed.append({'qty': take, 'buy_price': buy_price, 'pnl': pnl})
        qty_to_sell -= take
    return realized_pnl, consumed


def aggregate_portfolio_for_user(user):
    from .models import Trade
    from .samco_client import get_quote
    holdings = {}
    trades_qs = Trade.objects.filter(user=user).select_related('stock').order_by('timestamp')
    trades_by_stock = defaultdict(list)
    for t in trades_qs:
        trades_by_stock[t.stock.symbol].append(t)

    for sym, trades in trades_by_stock.items():
        # remaining lots
        buy_lots = _build_remaining_buy_lots(trades)
        qty_remaining = sum(l['qty'] for l in buy_lots)
        avg_price = None
        if qty_remaining > 0:
            total_cost = sum(Decimal(l['price']) * l['qty'] for l in buy_lots)
            avg_price = (total_cost / qty_remaining).quantize(Decimal('0.01'))
        # realized pnl via scanning
        realized = Decimal('0.00')
        evolving = []
        for t in trades:
            if t.trade_type == Trade.BUY:
                evolving.append({'qty': int(t.quantity), 'price': Decimal(t.price)})
            else:
                qty = int(t.quantity)
                while qty > 0 and evolving:
                    lot = evolving[0]
                    take = min(lot['qty'], qty)
                    realized += (Decimal(t.price) - lot['price']) * take
                    lot['qty'] -= take
                    qty -= take
                    if lot['qty'] == 0:
                        evolving.pop(0)
        stock_obj = trades[0].stock
        current_price = None
        try:
            current_price = get_quote(stock_obj.symbol, exchange='NSE')
        except Exception:
            current_price = None
        unrealized = Decimal('0.00')
        if current_price is not None and qty_remaining > 0 and avg_price is not None:
            unrealized = (Decimal(current_price) - avg_price) * qty_remaining
        holdings[sym] = {
            'stock': stock_obj,
            'quantity': qty_remaining,
            'avg_price': avg_price,
            'realized_pnl': realized.quantize(Decimal('0.01')),
            'unrealized_pnl': unrealized.quantize(Decimal('0.01')),
            'current_price': current_price
        }
    return holdings


def aggregate_portfolio(portfolio):
    from .models import Trade
    from .samco_client import get_quote
    from decimal import Decimal
    from collections import defaultdict

    holdings = {}
    trades_qs = Trade.objects.filter(portfolio=portfolio).select_related('stock').order_by('timestamp')
    trades_by_stock = defaultdict(list)

    for t in trades_qs:
        trades_by_stock[t.stock.symbol].append(t)

    # (same logic as before, but per portfolio)

    for sym, trades in trades_by_stock.items():
        # remaining lots
        buy_lots = _build_remaining_buy_lots(trades)
        qty_remaining = sum(l['qty'] for l in buy_lots)
        avg_price = None
        if qty_remaining > 0:
            total_cost = sum(Decimal(l['price']) * l['qty'] for l in buy_lots)
            avg_price = (total_cost / qty_remaining).quantize(Decimal('0.01'))
        # realized pnl via scanning
        realized = Decimal('0.00')
        evolving = []
        for t in trades:
            if t.trade_type == Trade.BUY:
                evolving.append({'qty': int(t.quantity), 'price': Decimal(t.price)})
            else:
                qty = int(t.quantity)
                while qty > 0 and evolving:
                    lot = evolving[0]
                    take = min(lot['qty'], qty)
                    realized += (Decimal(t.price) - lot['price']) * take
                    lot['qty'] -= take
                    qty -= take
                    if lot['qty'] == 0:
                        evolving.pop(0)
        stock_obj = trades[0].stock
        current_price = None
        try:
            current_price = get_quote(stock_obj.symbol, exchange='NSE')
        except Exception:
            current_price = None
        unrealized = Decimal('0.00')
        if current_price is not None and qty_remaining > 0 and avg_price is not None:
            unrealized = (Decimal(current_price) - avg_price) * qty_remaining
        holdings[sym] = {
            'stock': stock_obj,
            'quantity': qty_remaining,
            'avg_price': avg_price,
            'realized_pnl': realized.quantize(Decimal('0.01')),
            'unrealized_pnl': unrealized.quantize(Decimal('0.01')),
            'current_price': current_price
        }
    return holdings
