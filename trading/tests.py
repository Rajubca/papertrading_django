from django.test import TestCase
from django.contrib.auth.models import User
from trading.models import Portfolio, Stock, Holding, Transaction, PortfolioReport
from trading.views import update_portfolio_after_trade, generate_excel_report
from decimal import Decimal

class TradingTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='password')
        self.portfolio = Portfolio.objects.create(user=self.user, name='Test Portfolio', cash_balance=100000)
        self.stock = Stock.objects.create(symbol='TEST', name='Test Stock', current_price=100)

    def test_short_selling_logic(self):
        # 1. Buy 10 @ 100
        update_portfolio_after_trade(self.portfolio, self.stock, 10, 100, 'BUY')
        h = Holding.objects.get(portfolio=self.portfolio, stock=self.stock)
        self.assertEqual(h.quantity, 10)
        self.assertEqual(h.average_buy_price, 100)
        self.assertEqual(self.portfolio.cash_balance, 99000)

        # 2. Sell 5 @ 110 (Partial Close)
        update_portfolio_after_trade(self.portfolio, self.stock, 5, 110, 'SELL')
        h.refresh_from_db()
        self.assertEqual(h.quantity, 5)
        self.assertEqual(h.average_buy_price, 100)
        self.assertEqual(self.portfolio.cash_balance, 99550)

        # 3. Sell 10 @ 120 (Flip to Short)
        update_portfolio_after_trade(self.portfolio, self.stock, 10, 120, 'SELL')
        h.refresh_from_db()
        self.assertEqual(h.quantity, -5)
        self.assertEqual(h.average_buy_price, 120)
        self.assertEqual(self.portfolio.cash_balance, 100750)

        # 4. Buy 2 @ 110 (Partial Cover)
        update_portfolio_after_trade(self.portfolio, self.stock, 2, 110, 'BUY')
        h.refresh_from_db()
        self.assertEqual(h.quantity, -3)
        self.assertEqual(h.average_buy_price, 120)
        self.assertEqual(self.portfolio.cash_balance, 100530)

    def test_report_generation(self):
        update_portfolio_after_trade(self.portfolio, self.stock, 10, 100, 'BUY')
        report = self.portfolio.generate_report()
        self.assertEqual(report.total_value, self.portfolio.total_value)

        # Test Excel generation
        response = generate_excel_report(report)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        self.assertTrue(len(response.content) > 0)
