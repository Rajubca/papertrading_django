import json

# trading/views.py
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test


# trading/views.py
# trading/views.py


# trading/views.py
@login_required
def dashboard(request):
    # Get portfolio ID from query parameter or session
    portfolio_id = request.GET.get('portfolio') or request.session.get('active_portfolio_id')

    # Get all VISIBLE portfolios for the current user
    portfolios = Portfolio.objects.filter(
        user=request.user,
        visibility='PUBLIC'
    )

    # If no portfolios exist, render template with empty context
    if not portfolios.exists():
        return render(request, 'trading/dashboard.html', {
            'portfolios': None,
            'holdings': [],
            'transactions': [],
            'performance_data': json.dumps([])
        })

    # Get the selected portfolio or default to first
    if portfolio_id:
        try:
            portfolio = portfolios.get(id=portfolio_id)
        except Portfolio.DoesNotExist:
            portfolio = portfolios.first()
    else:
        portfolio = portfolios.first()

    # Store the active portfolio in session
    request.session['active_portfolio_id'] = portfolio.id

    # Get holdings for this portfolio
    holdings = Holding.objects.filter(portfolio=portfolio)

    # Get recent transactions (last 10)
    transactions = Transaction.objects.filter(portfolio=portfolio).order_by('-timestamp')[:10]

    # Generate performance data (last 30 days)
    performance_data = generate_performance_data(portfolio)

    # Calculate values without modifying the model instance
    total_value = portfolio.cash_balance + portfolio.invested_value

    # Check if initial_cash attribute exists
    if hasattr(portfolio, 'initial_cash'):
        initial_cash = portfolio.initial_cash
    else:
        initial_cash = portfolio.cash_balance + portfolio.invested_value

    profit_loss = total_value - initial_cash

    if initial_cash:
        profit_loss_percentage = (profit_loss / initial_cash * Decimal('100')).quantize(Decimal('0.01'))
    else:
        profit_loss_percentage = Decimal('0.00')

    context = {
        'portfolio': portfolio,
        'portfolios': portfolios,
        'holdings': holdings,
        'transactions': transactions,
        'performance_data': json.dumps(performance_data),
        'total_value': total_value,
        'profit_loss': profit_loss,
        'profit_loss_percentage': profit_loss_percentage,
        'initial_cash': initial_cash,
    }

    return render(request, 'trading/dashboard.html', context)


def generate_performance_data(portfolio):
    # Calculate total value for the portfolio
    total_value = float(portfolio.cash_balance + portfolio.invested_value)

    performance_data = []
    today = timezone.now().date()

    for i in range(30, 0, -1):
        date = today - timedelta(days=i)
        # Use float for calculation, then convert back to Decimal
        value = total_value * (0.95 + 0.1 * (i / 30))  # Mock data
        performance_data.append({
            "date": date.isoformat(),
            "value": round(value, 2)  # This will be a float in the JSON
        })

    return performance_data


def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('trading:dashboard')
    else:
        form = UserCreationForm()
    return render(request, 'registration/signup.html', {'form': form})


# trading/views.py
from django.db.models import Q
from django.contrib.auth.decorators import login_required


@login_required
def stock_list(request):
    stocks = Stock.objects.all()
    query = request.GET.get('q')

    if query:
        # Search by symbol or name (case-insensitive)
        stocks = stocks.filter(
            Q(symbol__icontains=query) |
            Q(name__icontains=query)
        )

    context = {
        'stocks': stocks,
        'query': query,
    }
    return render(request, 'trading/stock_list.html', context)


def stock_search(request):
    # API endpoint for AJAX search (if you want live search)
    query = request.GET.get('q', '')

    if query:
        stocks = Stock.objects.filter(
            Q(symbol__icontains=query) |
            Q(name__icontains=query)
        )[:10]  # Limit to 10 results
    else:
        stocks = Stock.objects.none()

    # Return JSON response for AJAX calls
    from django.http import JsonResponse
    results = []
    for stock in stocks:
        results.append({
            'id': stock.id,
            'symbol': stock.symbol,
            'name': stock.name,
            'current_price': str(stock.current_price),
        })

    return JsonResponse(results, safe=False)


@login_required
def stock_detail(request, pk):
    stock = get_object_or_404(Stock, pk=pk)

    # Get user's holdings for this stock
    user_holdings = Holding.objects.filter(
        portfolio__user=request.user,
        stock=stock
    )

    # Recent transactions
    if request.user.is_staff or request.user.is_superuser:
        # Admin: see all users' transactions for this stock
        recent_transactions = Transaction.objects.filter(
            stock=stock
        ).order_by('-timestamp')[:10]
    else:
        # Normal user: only their transactions
        recent_transactions = Transaction.objects.filter(
            portfolio__user=request.user,
            stock=stock
        ).order_by('-timestamp')[:10]

    context = {
        'stock': stock,
        'user_holdings': user_holdings,
        'recent_transactions': recent_transactions,
    }
    return render(request, 'trading/stock_detail.html', context)


#
# @login_required
# def trade_stock(request, stock_id=None):
#     portfolio = get_object_or_404(Portfolio, user=request.user)
#     if request.method == 'POST':
#         form = TradeForm(request.POST)
#         if form.is_valid():
#             stock = form.cleaned_data['stock']
#             transaction_type = form.cleaned_data['transaction_type']
#             quantity = form.cleaned_data['quantity']
#             notes = form.cleaned_data['notes']
#
#             total_cost = stock.current_price * quantity
#             if transaction_type == 'BUY':
#                 if portfolio.cash_balance < total_cost:
#                     messages.error(request, "Insufficient funds for this purchase")
#                     return redirect('trading:trade')
#                 portfolio.cash_balance -= total_cost
#             else:  # SELL
#                 holding = Holding.objects.filter(portfolio=portfolio, stock=stock).first()
#                 if not holding or holding.quantity < quantity:
#                     messages.error(request, "Insufficient shares to sell")
#                     return redirect('trading:trade')
#                 portfolio.cash_balance += total_cost
#
#             holding, created = Holding.objects.get_or_create(
#                 portfolio=portfolio,
#                 stock=stock,
#                 defaults={'quantity': 0, 'average_buy_price': stock.current_price}
#             )
#             if transaction_type == 'BUY':
#                 if holding.quantity > 0:
#                     holding.average_buy_price = (
#                             (holding.average_buy_price * holding.quantity + total_cost) /
#                             (holding.quantity + quantity)
#                     )
#                 holding.quantity += quantity
#             else:  # SELL
#                 holding.quantity -= quantity
#                 if holding.quantity == 0:
#                     holding.delete()
#                 else:
#                     holding.save()
#
#             portfolio.save()
#             if holding.quantity > 0:
#                 holding.save()
#
#             Transaction.objects.create(
#                 portfolio=portfolio,
#                 stock=stock,
#                 transaction_type=transaction_type,
#                 quantity=quantity,
#                 price_per_share=stock.current_price,
#                 notes=notes
#             )
#             messages.success(request, f"Successfully {transaction_type.lower()}ed {quantity} shares of {stock.symbol}")
#             return redirect('trading:dashboard')
#     else:
#         form = TradeForm()
#
#     context = {
#         'form': form,
#         'portfolio': portfolio
#     }
#     return render(request, 'trading/trade.html', context)

# trading/views.py
@login_required
def transaction_list(request):
    # Get portfolio ID from query parameter or session
    portfolio_id = request.GET.get('portfolio') or request.session.get('active_portfolio_id')

    # Get all VISIBLE portfolios for the current user
    portfolios = Portfolio.objects.filter(
        user=request.user,
        visibility='PUBLIC'
    )

    if not portfolios.exists():
        return render(request, 'trading/transaction_list.html', {
            'transactions': [],
            'portfolios': None
        })

    # Get the selected portfolio or default to first
    if portfolio_id:
        try:
            portfolio = portfolios.get(id=portfolio_id)
        except Portfolio.DoesNotExist:
            portfolio = portfolios.first()
    else:
        portfolio = portfolios.first()

    transactions = portfolio.transactions.all().select_related('stock').order_by('-timestamp')

    context = {
        'transactions': transactions,
        'portfolio': portfolio,
        'portfolios': portfolios,
    }

    return render(request, 'trading/transaction_list.html', context)


@login_required
def reports(request):
    """
    Displays a list of all portfolio reports for the current user.
    """
    # Get all portfolios for the current user
    user_portfolios = Portfolio.objects.filter(user=request.user)

    # Get all reports related to those portfolios
    reports = PortfolioReport.objects.filter(portfolio__in=user_portfolios).order_by('-report_date', '-created_at')

    context = {
        'reports': reports,
    }
    return render(request, 'trading/reports.html', context)


@login_required
def watchlists(request):
    watchlists = request.user.watchlists.all().prefetch_related('stocks')
    form = WatchlistForm()

    if request.method == 'POST':
        form = WatchlistForm(request.POST)
        if form.is_valid():
            watchlist = form.save(commit=False)
            watchlist.user = request.user
            watchlist.save()
            form.save_m2m()
            messages.success(request, f"Watchlist '{watchlist.name}' created")
            return redirect('watchlists')

    context = {'watchlists': watchlists, 'form': form}
    if request.htmx:
        return render(request, 'trading/partials/watchlist_list.html', context)
    return render(request, 'trading/watchlists.html', context)


@login_required
def update_stock_price(request, pk):
    if request.method == 'POST' and request.htmx:
        stock = get_object_or_404(Stock, pk=pk)
        new_price = Decimal(request.POST.get('price'))
        stock.update_price(new_price)
        return render(request, 'trading/partials/stock_price.html', {'stock': stock})
    return JsonResponse({'error': 'Invalid request'}, status=400)


# def stock_search(request):
#     query = request.GET.get('q', '')
#     stocks = Stock.objects.filter(
#         models.Q(symbol__icontains=query) |
#         models.Q(name__icontains=query)
#     )[:10]
#     return render(request, 'trading/partials/stock_search_results.html', {'stocks': stocks})
#

from django.contrib.auth.decorators import login_required
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Save additional profile fields
            profile = user.profile
            profile.phone = form.cleaned_data.get('phone')
            profile.birth_date = form.cleaned_data.get('birth_date')
            profile.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}!')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'registration/register.html', {'form': form})


# trading/views.py
from django.contrib.admin.views.decorators import staff_member_required


@staff_member_required
def manage_portfolio_visibility(request):
    """
    Admin view to manage portfolio visibility across all users
    """
    if request.method == 'POST':
        # Handle visibility updates
        portfolio_id = request.POST.get('portfolio_id')
        visibility = request.POST.get('visibility')

        if portfolio_id and visibility:
            portfolio = get_object_or_404(Portfolio, id=portfolio_id)
            portfolio.visibility = visibility
            portfolio.save()
            messages.success(request, f"Updated visibility for {portfolio.name}")

    # Get all portfolios with user information
    portfolios = Portfolio.objects.all().select_related('user').order_by('user__username', 'name')

    context = {
        'portfolios': portfolios,
    }
    return render(request, 'trading/admin_portfolio_visibility.html', context)


@login_required
def profile(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, instance=request.user.profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            messages.success(request, 'Your account has been updated!')
            return redirect('profile')
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'registration/profile.html', context)


from django.contrib.auth.decorators import login_required

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
import io


def portfolio_list(request):
    """
    Displays a list of all VISIBLE portfolios for the logged-in user.
    """
    portfolios = Portfolio.objects.filter(
        user=request.user,
        visibility='PUBLIC'  # Only show visible portfolios
    )
    context = {
        'portfolios': portfolios
    }
    return render(request, 'trading/portfolio_list.html', context)


@login_required
def create_portfolio(request):
    if request.method == 'POST':
        form = PortfolioForm(request.POST)
        if form.is_valid():
            new_portfolio = form.save(commit=False)
            new_portfolio.user = request.user
            new_portfolio.save()
            messages.success(request, f"Portfolio '{new_portfolio.name}' created successfully!")
            return redirect('trading:portfolio_list')
    else:
        form = PortfolioForm()

    context = {
        'form': form,
    }
    return render(request, 'trading/create_portfolio.html', context)


@login_required
def delete_portfolio(request, pk):
    portfolio = get_object_or_404(Portfolio, pk=pk, user=request.user)
    if request.method == 'POST':
        portfolio.delete()
        messages.success(request, f"Portfolio '{portfolio.name}' deleted successfully.")
        return redirect('trading:portfolio_list')

    context = {
        'portfolio': portfolio,
    }
    return render(request, 'trading/delete_portfolio.html', context)


@login_required
def report_detail(request, pk):
    report = get_object_or_404(PortfolioReport, pk=pk, portfolio__user=request.user)

    # Get recent transactions for this portfolio (last 10)
    recent_transactions = Transaction.objects.filter(
        portfolio=report.portfolio
    ).select_related('stock').order_by('-timestamp')[:10]

    # Check if PDF/print version is requested
    if request.GET.get('export') == 'pdf':
        return render(request, 'trading/report_pdf.html', {
            'report': report,
            'recent_transactions': recent_transactions,
            'generated_date': timezone.now(),
            'is_print_view': True
        })

    # Normal HTML view
    return render(request, 'trading/report_detail.html', {
        'report': report,
        'recent_transactions': recent_transactions
    })


from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.contrib.auth.decorators import login_required


@login_required
@require_GET
def stock_transactions_api(request, stock_id):
    try:
        from .models import Stock, Transaction, PortfolioReport

        # Get the stock
        stock = Stock.objects.get(id=stock_id)

        # Get the report ID from query parameters
        report_id = request.GET.get('report_id')

        if report_id:
            # Get transactions for this stock in the specific report period
            report = PortfolioReport.objects.get(id=report_id, portfolio__user=request.user)

            # Get transactions before the report date for this stock
            transactions = Transaction.objects.filter(
                portfolio=report.portfolio,
                stock=stock,
                timestamp__lte=report.report_date
            ).order_by('-timestamp')[:20]  # Last 20 transactions
        else:
            # Get all transactions for this stock
            transactions = Transaction.objects.filter(
                portfolio__user=request.user,
                stock=stock
            ).order_by('-timestamp')[:20]

        transactions_data = []
        for transaction in transactions:
            transactions_data.append({
                'timestamp': transaction.timestamp.isoformat(),
                'transaction_type': transaction.transaction_type,
                'quantity': transaction.quantity,
                'price_per_share': float(transaction.price_per_share),
                'total_cost': float(transaction.total_cost),
                'notes': transaction.notes
            })

        return JsonResponse({
            'success': True,
            'stock_symbol': stock.symbol,
            'transactions': transactions_data
        })

    except Stock.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Stock not found'}, status=404)
    except PortfolioReport.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Report not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def generate_pdf_report(report):
    """Generate PDF report using reportlab"""
    # Create a file-like buffer to receive PDF data
    buffer = io.BytesIO()

    # Create the PDF object, using the buffer as its "file"
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)

    # Container for the 'Flowable' objects
    elements = []
    styles = getSampleStyleSheet()

    # Add title
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        alignment=1,  # center
        spaceAfter=30,
        textColor=colors.HexColor('#2c3e50')
    )
    elements.append(Paragraph(f"Portfolio Report - {report.report_date}", title_style))

    # Portfolio summary
    elements.append(Paragraph("Portfolio Summary", styles['Heading2']))

    # Summary table
    summary_data = [
        ['Total Portfolio Value', f'₹{report.total_value:,.2f}'],
        ['Cash Balance', f'₹{report.cash_balance:,.2f}'],
        ['Invested Value', f'₹{report.investment_value:,.2f}'],
    ]

    # Add profit/loss if available
    if hasattr(report, 'profit_loss') and report.profit_loss != 0:
        pl_text = f'₹{abs(report.profit_loss):,.2f} ({abs(report.profit_loss_percentage):.2f}%)'
        pl_label = 'Profit' if report.profit_loss >= 0 else 'Loss'
        summary_data.append([f'{pl_label} since last report', pl_text])

    summary_table = Table(summary_data, colWidths=[3 * inch, 2 * inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 11),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 20))

    # Holdings breakdown
    if report.holding_reports.exists():
        elements.append(Paragraph("Holdings Breakdown", styles['Heading2']))

        holdings_data = [['Symbol', 'Qty', 'Avg Price', 'Current', 'Value', 'P/L']]

        for hr in report.holding_reports.all():
            pl_color = colors.green if hr.profit_loss >= 0 else colors.red
            holdings_data.append([
                hr.holding.stock.symbol,
                str(hr.quantity),
                f'₹{hr.average_price:.2f}',
                f'₹{hr.current_price:.2f}',
                f'₹{hr.current_value:,.2f}',
                f'₹{hr.profit_loss:.2f} ({hr.profit_loss_percentage:.2f}%)'
            ])

        holdings_table = Table(holdings_data, repeatRows=1,
                               colWidths=[0.8 * inch, 0.6 * inch, 1 * inch, 1 * inch, 1.2 * inch, 1.5 * inch])
        holdings_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#34495e')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#ecf0f1')),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('TEXTCOLOR', (5, 1), (5, -1), colors.green),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#bdc3c7')),
        ]))

        elements.append(holdings_table)
        elements.append(Spacer(1, 10))

        # Total investment
        total_data = [['Total Investment', f'₹{report.investment_value:,.2f}']]
        total_table = Table(total_data, colWidths=[4 * inch, 2 * inch])
        total_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2c3e50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
        ]))
        elements.append(total_table)

    # Build PDF
    doc.build(elements)

    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()

    response = HttpResponse(pdf, content_type='application/pdf')
    filename = f"portfolio_report_{report.report_date}_{report.portfolio.user.username}.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    return response


@login_required
def generate_report(request):
    portfolio = Portfolio.objects.filter(user=request.user).first()

    try:
        report = portfolio.generate_report()
        messages.success(request, f"Report generated for {report.report_date}")
        return redirect('trading:report_detail', pk=report.id)
    except Exception as e:
        messages.error(request, f"Error generating report: {str(e)}")
        return redirect('trading:reports')


from django.contrib.auth.decorators import login_required


# Helper function to check if user is admin
def is_admin(user):
    return user.is_superuser


@login_required
@user_passes_test(is_admin, redirect_field_name=None, login_url='trading:dashboard')
def download_nse_data(request):
    downloaded_files = get_downloaded_files()

    if request.method == 'POST':
        index_name = request.POST.get('index_name')
        if not index_name or index_name not in ['NIFTY 50', 'Securities in F&O']:
            messages.error(request, "Please select a valid index (NIFTY 50 or Securities in F&O)")
            return redirect('trading:data_download')

        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"{index_name.replace(' ', '_')}_{timestamp}.csv"
        save_path = os.path.join(settings.BASE_DIR, 'data', 'nse', file_name)

        success = download_nse_csv(index_name, save_path)
        if success:
            messages.success(request, f"Successfully downloaded {index_name} data")
            try:
                created_count, updated_count, skipped_count = process_nse_csv(save_path)
                messages.success(request,
                                 f"Updated stocks: {created_count} created, {updated_count} updated, {skipped_count} skipped due to invalid data")
            except Exception as e:
                messages.error(request, f"Failed to process CSV: {str(e)}")
        else:
            messages.error(request, f"Failed to download {index_name} data")

        return redirect('trading:data_download')

    context = {
        'downloaded_files': downloaded_files
    }
    return render(request, 'trading/data_download.html', context)


def download_nse_csv(index_name, save_path):
    """
    Downloads index data as CSV from NSE
    """
    url = (
        "https://www.nseindia.com/api/equity-stockIndices"
        f"?csv=true&index={index_name.replace(' ', '%20').replace('&', '%26')}"
        "&selectValFormat=crores"
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/market-data/live-equity-market",
    }

    try:
        with requests.Session() as session:
            session.get("https://www.nseindia.com/market-data/live-equity-market", headers=headers)
            response = session.get(url, headers=headers)
            response.raise_for_status()

            os.makedirs(os.path.dirname(save_path), exist_ok=True)

            with open(save_path, "wb") as f:
                f.write(response.content)

        return True
    except Exception as e:
        print(f"Failed to download {index_name}: {str(e)}")
        return False


def get_downloaded_files():
    data_dir = os.path.join(settings.BASE_DIR, 'data', 'nse')
    downloaded_files = []
    os.makedirs(data_dir, exist_ok=True)
    csv_files = glob.glob(os.path.join(data_dir, '*.csv'))
    for file_path in csv_files:
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        modified_time = os.path.getmtime(file_path)
        size_mb = file_size / (1024 * 1024)
        downloaded_files.append({
            'name': file_name,
            'size': f"{size_mb:.2f} MB",
            'path': file_path,
            'modified': modified_time
        })
    return downloaded_files


@login_required
def view_file(request, filename):
    """
    Returns the content of a downloaded CSV file
    """
    file_path = os.path.join(settings.BASE_DIR, 'data', 'nse', filename)

    if not os.path.exists(file_path):
        return HttpResponse("File not found", status=404)

    # Basic security check
    if not filename.endswith('.csv') or '..' in filename or '/' in filename:
        return HttpResponse("Invalid file", status=400)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return HttpResponse(content, content_type='text/plain')
    except Exception as e:
        return HttpResponse(f"Error reading file: {str(e)}", status=500)


def process_nse_csv(file_path):
    try:
        df = pd.read_csv(file_path, encoding='utf-8', skipinitialspace=True)
        df.columns = df.columns.str.strip().str.upper()
        if 'SYMBOL' not in df.columns:
            raise ValueError("CSV file missing 'SYMBOL' column")

        created_count = 0
        updated_count = 0
        skipped_count = 0
        for index, row in df.iterrows():
            symbol = row['SYMBOL']
            if not symbol or pd.isna(symbol):
                print(f"Skipping row {index}: Invalid or missing symbol")
                skipped_count += 1
                continue

            # Handle price conversion safely
            price = row.get('LTP', row.get('PREV_CLOSE', row.get('PREV. CLOSE', '0.0')))
            try:
                price = str(price).replace(',', '')  # Remove commas (e.g., "1,234.56" -> "1234.56")
                price_decimal = Decimal(price)
            except (InvalidOperation, ValueError, TypeError) as e:
                print(f"Skipping row {index} for symbol {symbol}: Invalid price '{price}' ({str(e)})")
                skipped_count += 1
                continue

            stock, created = Stock.objects.get_or_create(
                symbol=symbol,
                defaults={
                    'name': row.get('COMPANY_NAME', row.get('SERIES', symbol)),
                    'current_price': price_decimal,
                    'sector': row.get('INDUSTRY', row.get('SECTOR', None)),
                    'exchange': 'NSE'
                }
            )
            if created:
                created_count += 1
            else:
                stock.name = row.get('COMPANY_NAME', row.get('SERIES', stock.name))
                stock.current_price = price_decimal
                stock.sector = row.get('INDUSTRY', row.get('SECTOR', stock.sector))
                stock.exchange = 'NSE'
                stock.save()
                updated_count += 1

        print(f"Processed CSV: {created_count} stocks created, {updated_count} stocks updated, {skipped_count} skipped")
        return created_count, updated_count, skipped_count

    except Exception as e:
        print(f"Error processing CSV: {str(e)}")
        raise Exception(f"Error processing CSV: {str(e)}")


@login_required
@user_passes_test(is_admin, redirect_field_name=None, login_url='trading:dashboard')
def download_nse_data(request):
    downloaded_files = get_downloaded_files()

    if request.method == 'POST':
        index_name = request.POST.get('index_name')
        if not index_name:
            messages.error(request, "No index selected")
            return redirect('trading:data_download')

        timestamp = timezone.now().strftime('%Y%m%d_%H%M%S')
        file_name = f"{index_name.replace(' ', '_')}_{timestamp}.csv"
        save_path = os.path.join(settings.BASE_DIR, 'data', 'nse', file_name)

        success = download_nse_csv(index_name, save_path)
        if success:
            messages.success(request, f"Successfully downloaded {index_name} data")
            try:
                # Corrected line to unpack all three values
                created_count, updated_count, skipped_count = process_nse_csv(save_path)
                messages.success(request,
                                 f"Updated stocks: {created_count} created, {updated_count} updated, {skipped_count} skipped due to invalid data")
            except Exception as e:
                messages.error(request, f"Failed to process CSV: {str(e)}")
        else:
            messages.error(request, f"Failed to download {index_name} data")

        return redirect('trading:data_download')

    context = {
        'downloaded_files': downloaded_files
    }
    return render(request, 'trading/data_download.html', context)


def download_nse_csv(index_name, save_path):
    url = (
        "https://www.nseindia.com/api/equity-stockIndices"
        f"?csv=true&index={index_name.replace(' ', '%20').replace('&', '%26')}"
        "&selectValFormat=crores"
    )
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/market-data/live-equity-market",
    }
    try:
        with requests.Session() as session:
            session.get("https://www.nseindia.com/market-data/live-equity-market", headers=headers)
            response = session.get(url, headers=headers)
            response.raise_for_status()
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(response.content)
        return True
    except Exception as e:
        print(f"Failed to download {index_name}: {str(e)}")
        return False


# trading/views.py

from decimal import InvalidOperation
from datetime import timedelta
from django.contrib.auth.forms import UserCreationForm
import os
import glob
import requests
import pandas as pd
from django.conf import settings
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse, HttpResponse
from decimal import Decimal
from .models import Holding, PortfolioReport
from .forms import WatchlistForm, PortfolioForm  # Make sure to import PortfolioForm


# ... (rest of your existing views)

@login_required
def portfolio_list(request):
    """
    Displays a list of all portfolios for the logged-in user.
    """
    portfolios = Portfolio.objects.filter(user=request.user)
    context = {
        'portfolios': portfolios
    }
    return render(request, 'trading/portfolio_list.html', context)


@login_required
def create_portfolio(request):
    """
    Handles the creation of a new portfolio.
    """
    if request.method == 'POST':
        form = PortfolioForm(request.POST)
        if form.is_valid():
            portfolio = form.save(commit=False)
            portfolio.user = request.user
            portfolio.save()
            messages.success(request, f"Portfolio '{portfolio.name}' created successfully!")
            return redirect('trading:portfolio_list')
    else:
        form = PortfolioForm()

    context = {'form': form}
    return render(request, 'trading/create_portfolio.html', context)


@login_required
def delete_portfolio(request, pk):
    """
    Handles the deletion of a specific portfolio.
    Uses POST to prevent accidental deletion from a GET request.
    """
    portfolio = get_object_or_404(Portfolio, pk=pk, user=request.user)
    if request.method == 'POST':
        # Delete the portfolio and all related holdings and transactions
        portfolio.delete()
        messages.success(request, f"Portfolio '{portfolio.name}' deleted successfully.")
        return redirect('trading:portfolio_list')

    context = {'portfolio': portfolio}
    return render(request, 'trading/portfolio_confirm_delete.html', context)


# trading/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Stock, Portfolio, Transaction
from .forms import TradeForm


# trading/views.py
@login_required
def trade_stock(http_request, stock_id=None):
    """
    Handles stock trading functionality (buy/sell).
    """
    # Get all visible portfolios for the user
    portfolios = Portfolio.objects.filter(
        user=http_request.user,
        visibility='PUBLIC'
    )

    if not portfolios.exists():
        messages.error(http_request, "You need to create a portfolio first!")
        return redirect('trading:create_portfolio')

    # Get the selected portfolio from form or session
    portfolio_id = http_request.session.get('active_portfolio_id')
    portfolio = None

    if portfolio_id:
        try:
            portfolio = portfolios.get(id=portfolio_id)
        except Portfolio.DoesNotExist:
            portfolio = portfolios.first()
    else:
        portfolio = portfolios.first()

    # Get all stocks for the dropdown
    stocks = Stock.objects.all()

    # Initialize the form with initial data
    initial_data = {}
    selected_stock = None

    if stock_id:
        selected_stock = get_object_or_404(Stock, id=stock_id)
        initial_data['stock'] = selected_stock
        initial_data['price_per_share'] = float(selected_stock.current_price)

    if http_request.method == 'POST':
        form = TradeForm(http_request.POST, initial=initial_data, user=http_request.user)

        if form.is_valid():
            transaction = form.save(commit=False)
            selected_portfolio = form.cleaned_data['portfolio']
            transaction.portfolio = selected_portfolio
            transaction.user = http_request.user

            # Calculate total amount
            total_amount = transaction.quantity * transaction.price_per_share

            # Validate buy transaction
            if transaction.transaction_type == 'BUY':
                if selected_portfolio.cash_balance < total_amount:
                    messages.error(http_request, "Insufficient funds for this purchase!")
                    return render(http_request, 'trading/trade.html', {
                        'form': form,
                        'portfolio': selected_portfolio,
                        'portfolios': portfolios,
                        'stocks': stocks,
                        'selected_stock': selected_stock,
                        'stocks_count': stocks.count(),
                    })
                selected_portfolio.cash_balance -= total_amount
            else:  # SELL
                # Check if user has enough shares to sell
                try:
                    holding = Holding.objects.get(portfolio=selected_portfolio, stock=transaction.stock)
                    if holding.quantity < transaction.quantity:
                        messages.error(http_request,
                                       f"You only own {holding.quantity} shares of {transaction.stock.symbol}!")
                        return render(http_request, 'trading/trade.html', {
                            'form': form,
                            'portfolio': selected_portfolio,
                            'portfolios': portfolios,
                            'stocks': stocks,
                            'selected_stock': selected_stock,
                            'stocks_count': stocks.count(),
                        })
                except Holding.DoesNotExist:
                    messages.error(http_request, f"You don't own any shares of {transaction.stock.symbol}!")
                    return render(http_request, 'trading/trade.html', {
                        'form': form,
                        'portfolio': selected_portfolio,
                        'portfolios': portfolios,
                        'stocks': stocks,
                        'selected_stock': selected_stock,
                        'stocks_count': stocks.count(),
                    })

                selected_portfolio.cash_balance += total_amount

            # Save the transaction
            transaction.save()

            # Update or create holding
            holding, created = Holding.objects.get_or_create(
                portfolio=selected_portfolio,
                stock=transaction.stock,
                defaults={
                    'quantity': transaction.quantity,
                    'average_buy_price': transaction.price_per_share
                }
            )

            if not created:
                if transaction.transaction_type == 'BUY':
                    # Update average buy price for new purchases
                    total_cost = (holding.average_buy_price * holding.quantity) + total_amount
                    holding.quantity += transaction.quantity
                    holding.average_buy_price = total_cost / holding.quantity
                else:  # SELL
                    holding.quantity -= transaction.quantity
                    if holding.quantity <= 0:
                        holding.delete()
                        holding = None

                if holding:
                    holding.save()

            selected_portfolio.save()

            # Update session with active portfolio
            http_request.session['active_portfolio_id'] = selected_portfolio.id

            messages.success(http_request,
                             f"Successfully {transaction.transaction_type.lower()}ed {transaction.quantity} shares of {transaction.stock.symbol}")
            return redirect('trading:dashboard')
    else:
        form = TradeForm(initial=initial_data, user=http_request.user)
        # Set initial portfolio in form
        if portfolio:
            form.fields['portfolio'].initial = portfolio

    # If no stock is selected, pre-select the first stock for order summary
    if not selected_stock and stocks.exists():
        selected_stock = stocks.first()

    context = {
        'form': form,
        'portfolio': portfolio,
        'portfolios': portfolios,
        'stocks': stocks,
        'selected_stock': selected_stock,
        'stocks_count': stocks.count(),
        'portfolio_cash_balance': float(portfolio.cash_balance) if portfolio else 0
    }

    return render(http_request, 'trading/trade.html', context)


# trading/views.py
from django.views.decorators.http import require_POST

import json
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt  # Add this decorator to bypass CSRF for AJAX calls
@login_required
@require_POST
def calculate_order_summary(http_request):
    try:
        # Parse JSON data from request body
        if http_request.content_type == 'application/json':
            data = json.loads(http_request.body)
            stock_id = data.get("stock_id")
            quantity = data.get("quantity", 0)
            price = data.get("price", 0)
            transaction_type = data.get("transaction_type", "BUY")
            portfolio_id = data.get("portfolio_id")
        else:
            # Fallback to form data
            stock_id = http_request.POST.get("stock_id")
            quantity = http_request.POST.get("quantity", 0)
            price = http_request.POST.get("price", 0)
            transaction_type = http_request.POST.get("transaction_type", "BUY")
            portfolio_id = http_request.POST.get("portfolio_id")

        # Convert to appropriate types
        stock_id = int(stock_id) if stock_id else None
        quantity = int(quantity) if quantity else 0
        price = Decimal(str(price)) if price else Decimal('0')

        if not stock_id:
            return JsonResponse({"success": False, "error": "Stock ID is required"}, status=400)

        stock = get_object_or_404(Stock, id=stock_id)

        # Get the selected portfolio
        if portfolio_id:
            portfolio = get_object_or_404(Portfolio, id=portfolio_id, user=http_request.user, visibility='PUBLIC')
        else:
            # Fallback to first portfolio
            portfolio = Portfolio.objects.filter(
                user=http_request.user,
                visibility='PUBLIC'
            ).first()
            if not portfolio:
                return JsonResponse({"success": False, "error": "No portfolio found"}, status=400)

        total_amount = quantity * price

        # Calculate cash after transaction
        if transaction_type == 'BUY':
            cash_after = portfolio.cash_balance - total_amount
        else:  # SELL
            cash_after = portfolio.cash_balance + total_amount

        # Check available shares for sell transactions
        owned_shares = 0
        if transaction_type == 'SELL':
            try:
                holding = Holding.objects.get(portfolio=portfolio, stock=stock)
                owned_shares = holding.quantity
            except Holding.DoesNotExist:
                owned_shares = 0

        response_data = {
            "success": True,
            "quantity": quantity,
            "price": float(price),
            "total": float(total_amount),
            "cash_after": float(cash_after),
            "current_price": float(stock.current_price),
            "owned_shares": owned_shares,
            "portfolio_cash": float(portfolio.cash_balance)
        }

        return JsonResponse(response_data)

    except (ValueError, TypeError) as e:
        return JsonResponse({"success": False, "error": "Invalid input data: " + str(e)}, status=400)
    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)}, status=500)


@login_required
def get_stock_price_api(request, stock_id):
    try:
        stock = Stock.objects.get(id=stock_id)
        return JsonResponse({
            'success': True,
            'price': float(stock.current_price),
            'symbol': stock.symbol
        })
    except Stock.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Stock not found'
        }, status=404)


# trading/views.py
@staff_member_required
def portfolio_manager(request):
    """
    Comprehensive portfolio management for admins
    """
    # Filtering
    visibility_filter = request.GET.get('visibility', 'all')
    user_filter = request.GET.get('user', '')

    portfolios = Portfolio.objects.all().select_related('user').order_by('user__username', 'name')

    if visibility_filter != 'all':
        portfolios = portfolios.filter(visibility=visibility_filter)

    if user_filter:
        portfolios = portfolios.filter(user__username__icontains=user_filter)

    # Statistics
    total_portfolios = Portfolio.objects.count()
    public_portfolios = Portfolio.objects.filter(visibility='PUBLIC').count()
    private_portfolios = Portfolio.objects.filter(visibility='PRIVATE').count()

    context = {
        'portfolios': portfolios,
        'total_portfolios': total_portfolios,
        'public_portfolios': public_portfolios,
        'private_portfolios': private_portfolios,
        'visibility_filter': visibility_filter,
        'user_filter': user_filter,
    }
    return render(request, 'trading/portfolio_manager.html', context)


# trading/views.py
@staff_member_required
def bulk_update_visibility(request):
    """
    Bulk update portfolio visibility
    """
    if request.method == 'POST':
        visibility = request.POST.get('visibility')
        portfolio_ids = request.POST.getlist('portfolio_ids')

        if visibility and portfolio_ids:
            Portfolio.objects.filter(id__in=portfolio_ids).update(visibility=visibility)
            messages.success(request, f"Updated visibility for {len(portfolio_ids)} portfolios")

    return redirect('trading:portfolio_manager')


@staff_member_required
def toggle_portfolio_visibility(request, portfolio_id):
    """
    Toggle visibility for a single portfolio
    """
    portfolio = get_object_or_404(Portfolio, id=portfolio_id)

    if portfolio.visibility == 'PUBLIC':
        portfolio.visibility = 'PRIVATE'
        action = 'hidden'
    else:
        portfolio.visibility = 'PUBLIC'
        action = 'made visible'

    portfolio.save()
    messages.success(request, f"Portfolio '{portfolio.name}' has been {action}")

    return redirect('trading:portfolio_manager')


# trading/views.py
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import json


@csrf_exempt
@require_POST
@login_required
def calculate_order(request):
    """
    AJAX endpoint to calculate order details
    """
    try:
        data = json.loads(request.body)
        stock_id = data.get('stock_id')
        quantity = int(data.get('quantity', 0))
        price = float(data.get('price', 0))
        transaction_type = data.get('transaction_type', 'BUY')

        # Get stock and portfolio
        stock = get_object_or_404(Stock, id=stock_id)
        portfolio = Portfolio.objects.filter(user=request.user).first()

        if not portfolio:
            return JsonResponse({'error': 'No portfolio found'}, status=400)

        # Calculate values
        total_cost = quantity * price

        # Check if user has enough shares to sell
        if transaction_type == 'SELL':
            try:
                holding = Holding.objects.get(portfolio=portfolio, stock=stock)
                available_shares = holding.quantity
            except Holding.DoesNotExist:
                available_shares = 0

            if quantity > available_shares:
                return JsonResponse({
                    'error': f'Insufficient shares. You only own {available_shares} shares.'
                }, status=400)

        # Check if user has enough cash to buy
        if transaction_type == 'BUY' and total_cost > portfolio.cash_balance:
            return JsonResponse({
                'error': f'Insufficient funds. You need ₹{total_cost:.2f} but only have ₹{portfolio.cash_balance:.2f}.'
            }, status=400)

        # Calculate cash after transaction
        if transaction_type == 'BUY':
            cash_after = portfolio.cash_balance - total_cost
        else:  # SELL
            cash_after = portfolio.cash_balance + total_cost

        return JsonResponse({
            'success': True,
            'total_cost': total_cost,
            'cash_after': cash_after,
            'current_cash': portfolio.cash_balance,
            'can_execute': True
        })

    except (ValueError, TypeError) as e:
        return JsonResponse({'error': 'Invalid input data'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
