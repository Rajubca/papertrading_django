from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.db import transaction
from .models import Stock, Watchlist, Trade, Account, Portfolio
from .samco_client import get_quote, multi_quote
from .trading_utils import (
    available_quantity_for_user_stock,
    compute_realized_pnl_for_sell,
    aggregate_portfolio_for_user,
)


@login_required
def watchlist_view(request):
    watchlist, _ = Watchlist.objects.get_or_create(user=request.user, name='Default')
    stocks = list(watchlist.stocks.all())
    # fetch multi-quote
    symbols = [s.symbol.upper() for s in stocks if s.symbol]
    ltp_map = {}
    if symbols:
        try:
            ltp_map = multi_quote(symbols, exchange='NSE') or {}
        except Exception:
            ltp_map = {}
    for st in stocks:
        ltp = ltp_map.get(st.symbol.upper())
        if ltp is None:
            try:
                ltp = get_quote(st.symbol, exchange='NSE')
            except Exception:
                ltp = None
        if ltp is not None:
            st.current_price = Decimal(str(ltp))
            st.save(update_fields=['current_price', 'updated_at'])
    # account for summary card
    account, _ = Account.objects.get_or_create(user=request.user)
    return render(request, 'stocks/watchlist.html', {'watchlist': watchlist, 'stocks': stocks, 'account': account})


@login_required
def stock_detail_view(request, symbol):
    symbol = symbol.strip().upper()
    stock, _ = Stock.objects.get_or_create(symbol=symbol)
    ltp = None
    try:
        ltp = get_quote(stock.symbol, exchange='NSE')
    except Exception:
        ltp = None
    if ltp is not None:
        stock.current_price = Decimal(str(ltp))
        stock.save(update_fields=['current_price', 'updated_at'])
    watchlist, _ = Watchlist.objects.get_or_create(user=request.user, name='Default')
    in_watchlist = watchlist.stocks.filter(pk=stock.pk).exists()
    return render(request, 'stocks/stock_detail.html', {'stock': stock, 'in_watchlist': in_watchlist})


@require_POST
@login_required
def modify_watchlist(request):
    symbol = request.POST.get('symbol', '').strip().upper()
    action = request.POST.get('action')
    next_url = request.POST.get('next')
    if not symbol or action not in ('add', 'remove'):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Missing parameters'}, status=400)
        return HttpResponseBadRequest('Missing or invalid parameters')
    stock, _ = Stock.objects.get_or_create(symbol=symbol)
    watchlist, _ = Watchlist.objects.get_or_create(user=request.user, name='Default')
    if action == 'add':
        watchlist.stocks.add(stock)
    else:
        watchlist.stocks.remove(stock)
    in_watchlist = watchlist.stocks.filter(pk=stock.pk).exists()
    data = {
        'success': True,
        'action': action,
        'symbol': symbol,
        'in_watchlist': in_watchlist,
        'watchlist_count': watchlist.stocks.count(),
    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(data)
    if next_url:
        return redirect(next_url)
    return redirect(reverse('stocks:detail', kwargs={'symbol': symbol}))


@require_POST
@login_required
def place_trade_view(request):
    symbol = request.POST.get('symbol', '').strip().upper()
    qty_raw = request.POST.get('quantity')
    action = request.POST.get('action', '').strip().lower()
    price_override = request.POST.get('price')
    next_url = request.POST.get('next')
    if not symbol or not qty_raw or action not in ('buy', 'sell'):
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Missing parameters'}, status=400)
        return HttpResponseBadRequest('Missing parameters')
    try:
        qty = int(qty_raw)
        if qty <= 0:
            raise ValueError()
    except Exception:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'Invalid quantity'}, status=400)
        return HttpResponseBadRequest('Invalid quantity')
    stock, _ = Stock.objects.get_or_create(symbol=symbol)
    exec_price = None
    if price_override:
        try:
            exec_price = Decimal(price_override)
        except Exception:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Invalid price'}, status=400)
            return HttpResponseBadRequest('Invalid price')
    else:
        try:
            exec_price = get_quote(stock.symbol, exchange='NSE')
        except Exception:
            exec_price = None
    if exec_price is None:
        if stock.current_price:
            exec_price = Decimal(stock.current_price)
        else:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Could not determine execution price'}, status=400)
            return HttpResponseBadRequest('Could not determine execution price')
    account, _ = Account.objects.get_or_create(user=request.user)
    with transaction.atomic():
        if action == 'buy':
            total_cost = (Decimal(exec_price) * qty).quantize(Decimal('0.01'))
            if account.virtual_balance < total_cost:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'Insufficient balance'}, status=403)
                return HttpResponseForbidden('Insufficient virtual balance to place buy order')
            account.virtual_balance = (account.virtual_balance - total_cost).quantize(Decimal('0.01'))
            trade = Trade.objects.create(user=request.user, stock=stock, quantity=qty, price=Decimal(exec_price),
                                         trade_type=Trade.BUY)
            account.save(update_fields=['virtual_balance', 'total_pnl'])
            realized_pnl = Decimal('0.00')
        else:
            available = available_quantity_for_user_stock(request.user, stock)
            if available < qty:
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'error': 'Not enough shares'}, status=403)
                return HttpResponseForbidden('Not enough shares to sell')
            realized_pnl, consumed = compute_realized_pnl_for_sell(request.user, stock, qty, Decimal(exec_price))
            trade = Trade.objects.create(user=request.user, stock=stock, quantity=qty, price=Decimal(exec_price),
                                         trade_type=Trade.SELL)
            proceeds = (Decimal(exec_price) * qty).quantize(Decimal('0.01'))
            account.virtual_balance = (account.virtual_balance + proceeds).quantize(Decimal('0.01'))
            account.total_pnl = (account.total_pnl + realized_pnl).quantize(Decimal('0.01'))
            account.save(update_fields=['virtual_balance', 'total_pnl'])
    stock.current_price = Decimal(exec_price)
    stock.save(update_fields=['current_price', 'updated_at'])
    holdings = aggregate_portfolio_for_user(request.user)
    symbol_holding = holdings.get(stock.symbol, {})
    response_data = {
        'success': True,
        'trade': {
            'symbol': stock.symbol,
            'quantity': qty,
            'price': str(exec_price),
            'type': action.upper(),
            'timestamp': trade.timestamp.isoformat(),
        },
        'account': {
            'virtual_balance': str(account.virtual_balance),
            'total_pnl': str(account.total_pnl),
        },
        'holding': {
            'quantity': symbol_holding.get('quantity', 0),
            'avg_price': str(symbol_holding.get('avg_price')) if symbol_holding.get('avg_price') else None,
            'current_price': str(symbol_holding.get('current_price')) if symbol_holding.get('current_price') else None,
            'unrealized_pnl': str(symbol_holding.get('unrealized_pnl')) if symbol_holding.get(
                'unrealized_pnl') else None,
            'realized_pnl': str(symbol_holding.get('realized_pnl')) if symbol_holding.get('realized_pnl') else None,
        }
    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse(response_data)
    if next_url:
        return redirect(next_url)
    return redirect(reverse('stocks:portfolio'))


@login_required
def portfolio_view(request):
    holdings = aggregate_portfolio_for_user(request.user)
    account, _ = Account.objects.get_or_create(user=request.user)
    return render(request, 'stocks/portfolio.html', {'holdings': holdings, 'account': account})


@login_required
def orders_history_view(request):
    trades = Trade.objects.filter(user=request.user).select_related('stock').order_by('-timestamp')
    return render(request, 'stocks/orders.html', {'trades': trades})


@login_required
def portfolio_list(request):
    portfolios = request.user.portfolios.all()
    return render(request, "stocks/portfolio_list.html", {"portfolios": portfolios})


@login_required
def portfolio_create(request):
    if request.method == "POST":
        name = request.POST.get("name")
        Portfolio.objects.create(user=request.user, name=name)
        return redirect("stocks:portfolio")
    return render(request, "stocks/portfolio_form.html")


@login_required
def portfolio_edit(request, pk):
    portfolio = get_object_or_404(Portfolio, pk=pk, user=request.user)
    if request.method == "POST":
        portfolio.name = request.POST.get("name")
        portfolio.save()
        return redirect("portfolio_list")
    return render(request, "stocks/portfolio_form.html", {"portfolio": portfolio})


@login_required
def portfolio_delete(request, pk):
    portfolio = get_object_or_404(Portfolio, pk=pk, user=request.user)
    portfolio.delete()
    return redirect("portfolio_list")
