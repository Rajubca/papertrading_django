# trading/context_processors.py
from trading.models import Portfolio


def active_portfolio(request):
    if request.user.is_authenticated:
        portfolio_id = request.session.get('active_portfolio_id')
        if portfolio_id:
            try:
                portfolio = Portfolio.objects.get(
                    id=portfolio_id,
                    user=request.user,
                    visibility='PUBLIC'
                )
                return {'active_portfolio': portfolio}
            except Portfolio.DoesNotExist:
                pass

        # Fallback to first visible portfolio
        portfolios = Portfolio.objects.filter(
            user=request.user,
            visibility='PUBLIC'
        )
        if portfolios.exists():
            portfolio = portfolios.first()
            request.session['active_portfolio_id'] = portfolio.id
            return {'active_portfolio': portfolio}

    return {'active_portfolio': None}