from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from .models import Stock, Portfolio, Holding, Transaction, Watchlist, PortfolioReport
from .serializers import (
    StockSerializer, PortfolioSerializer, HoldingSerializer,
    TransactionSerializer, WatchlistSerializer, PortfolioReportSerializer
)
from django.contrib.auth.models import User
from datetime import date, timedelta


class StockViewSet(viewsets.ModelViewSet):
    queryset = Stock.objects.all()
    serializer_class = StockSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        stocks = Stock.objects.filter(
            models.Q(symbol__icontains=query) |
            models.Q(name__icontains=query)
        )[:10]
        serializer = self.get_serializer(stocks, many=True)
        return Response(serializer.data)


class PortfolioViewSet(viewsets.ModelViewSet):
    serializer_class = PortfolioSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Portfolio.objects.filter(user=self.request.user)

    @action(detail=True, methods=['get'])
    def holdings(self, request, pk=None):
        portfolio = self.get_object()
        holdings = portfolio.holdings.all()
        serializer = HoldingSerializer(holdings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        portfolio = self.get_object()
        transactions = portfolio.transactions.all()
        serializer = TransactionSerializer(transactions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        portfolio = self.get_object()

        # Generate performance data (last 30 days)
        end_date = date.today()
        start_date = end_date - timedelta(days=30)

        reports = PortfolioReport.objects.filter(
            portfolio=portfolio,
            report_date__range=[start_date, end_date]
        ).order_by('report_date')

        data = {
            'dates': [report.report_date.strftime('%Y-%m-%d') for report in reports],
            'values': [float(report.total_value) for report in reports],
            'cash': [float(report.cash_balance) for report in reports],
            'investments': [float(report.investment_value) for report in reports],
        }

        return Response(data)


class TransactionViewSet(viewsets.ModelViewSet):
    serializer_class = TransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Transaction.objects.filter(portfolio__user=self.request.user)

    def perform_create(self, serializer):
        portfolio = get_object_or_404(Portfolio, user=self.request.user)
        serializer.save(portfolio=portfolio)


class WatchlistViewSet(viewsets.ModelViewSet):
    serializer_class = WatchlistSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Watchlist.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ReportViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PortfolioReportSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return PortfolioReport.objects.filter(portfolio__user=self.request.user)