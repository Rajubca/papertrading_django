import os
import requests
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
import glob
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import PortfolioReport
from django.contrib.auth import login
from django.forms import models
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils import timezone
from django.views.generic import ListView, DetailView
from django.http import JsonResponse, HttpResponse
from django.urls import reverse
from django.db.models import Sum
from decimal import Decimal
from .models import Stock, Portfolio, Holding, Transaction, Watchlist, PortfolioReport
from .forms import TradeForm, StockForm, WatchlistForm
import random
from datetime import datetime, timedelta
from django.contrib.auth.forms import UserCreationForm
import pandas as pd
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Portfolio, Holding, Transaction
from datetime import timedelta


@login_required
def dashboard(request):
    # Get or create portfolio
    portfolio, created = Portfolio.objects.get_or_create(user=request.user)

    # Get holdings and recent transactions
    holdings = Holding.objects.filter(portfolio=portfolio).select_related('stock')
    transactions = Transaction.objects.filter(portfolio=portfolio).order_by('-timestamp')[:5]

    # Generate performance data (last 30 days)
    performance_data = []
    for i in range(30, -1, -1):
        date = (timezone.now() - timedelta(days=i)).strftime('%Y-%m-%d')
        value = float(portfolio.total_value()) * (0.95 + 0.1 * (i / 30))  # Simulated growth
        performance_data.append({
            'date': date,
            'value': round(value, 2)
        })

    context = {
        'portfolio': portfolio,
        'holdings': holdings,
        'transactions': transactions,
        'performance_data': performance_data,
    }
    return render(request, 'trading/dashboard.html', context)

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


@login_required
def stock_list(request):
    stocks = Stock.objects.all().order_by('symbol')
    form = StockForm()

    if request.htmx:
        if 'q' in request.GET:
            query = request.GET.get('q')
            stocks = stocks.filter(
                models.Q(symbol__icontains=query) |
                models.Q(name__icontains=query)
            )
        return render(request, 'trading/partials/stock_table.html', {'stocks': stocks})

    return render(request, 'trading/stock_list.html', {'stocks': stocks, 'form': form})


@login_required
def stock_detail(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    price_history = stock.get_price_history()

    context = {
        'stock': stock,
        'price_history': price_history,
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

@login_required
def transaction_list(request):
    portfolio = get_object_or_404(Portfolio, user=request.user)
    transactions = portfolio.transactions.all().select_related('stock')

    if request.htmx:
        return render(request, 'trading/partials/transaction_table.html', {'transactions': transactions})

    return render(request, 'trading/transaction_list.html', {'transactions': transactions})


@login_required
def reports(request):
    portfolio = get_object_or_404(Portfolio, user=request.user)
    reports = portfolio.reports.all()

    if request.method == 'POST':
        report = portfolio.generate_report()
        messages.success(request, f"Report generated for {report.report_date}")
        return redirect('reports')

    if request.htmx:
        return render(request, 'trading/partials/report_list.html', {'reports': reports})

    return render(request, 'trading/reports.html', {'reports': reports})


@login_required
def report_detail(request, pk):
    report = get_object_or_404(PortfolioReport, pk=pk, portfolio__user=request.user)
    return render(request, 'trading/report_detail.html', {'report': report})


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


def stock_search(request):
    query = request.GET.get('q', '')
    stocks = Stock.objects.filter(
        models.Q(symbol__icontains=query) |
        models.Q(name__icontains=query)
    )[:10]
    return render(request, 'trading/partials/stock_search_results.html', {'stocks': stocks})





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


@login_required
def reports(request):
    portfolio = request.user.portfolio
    reports = PortfolioReport.objects.filter(portfolio=portfolio).order_by('-report_date')
    return render(request, 'trading/reports.html', {'reports': reports})

@login_required
def report_detail(request, pk):
    report = get_object_or_404(PortfolioReport, pk=pk, portfolio__user=request.user)
    return render(request, 'trading/report_detail.html', {'report': report})

@login_required
def generate_report(request):
    portfolio = request.user.portfolio
    report = portfolio.generate_report()  # Assuming you have this method
    return redirect('trading:report_detail', pk=report.id)



# Helper function to check if user is admin
def is_admin(user):
    return user.is_superuser


@login_required
@user_passes_test(is_admin, redirect_field_name=None, login_url='trading:dashboard')  # Redirect
def download_nse_data(request):
    # Get list of downloaded files
    downloaded_files = get_downloaded_files()

    if request.method == 'POST':
        index_type = request.POST.get('index_type')

        indices = {
            'nifty50': ('NIFTY 50', 'nifty50.csv'),
            'fno': ('SECURITIES IN F&O', 'securities_fo.csv')
        }

        if index_type in indices:
            index_name, filename = indices[index_type]
            save_path = os.path.join(settings.BASE_DIR, 'data', 'nse', filename)

            if download_nse_csv(index_name, save_path):
                messages.success(request, f"{index_name} data downloaded successfully!")
                # Refresh the file list after download
                downloaded_files = get_downloaded_files()
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
    """
    Returns a list of downloaded CSV files with their metadata
    """
    data_dir = os.path.join(settings.BASE_DIR, 'data', 'nse')
    downloaded_files = []

    # Create directory if it doesn't exist
    os.makedirs(data_dir, exist_ok=True)

    # Check for CSV files
    csv_files = glob.glob(os.path.join(data_dir, '*.csv'))

    for file_path in csv_files:
        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        modified_time = os.path.getmtime(file_path)

        # Convert file size to human readable format
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
        import pandas as pd

        # Read CSV with flexible encoding
        try:
            df = pd.read_csv(file_path, encoding='utf-8', skipinitialspace=True)
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(file_path, encoding='latin-1', skipinitialspace=True)
            except:
                df = pd.read_csv(file_path, encoding='cp1252', skipinitialspace=True)

        # Clean column names
        df.columns = df.columns.str.strip().str.upper()

        print(f"Available columns in CSV: {list(df.columns)}")  # Debug: see what columns we have

        # Map NSE column names to our expected names
        column_mapping = {
            'SYMBOL': ['SYMBOL'],
            'LTP': ['LTP', 'LAST PRICE', 'LAST'],
            'PREVIOUS CLOSE': ['PREVIOUS CLOSE', 'PREV CLOSE', 'PREVIOUS_CLOSE'],
            'COMPANY NAME': ['COMPANY NAME', 'COMPANY_NAME', 'NAME'],
            'INDUSTRY': ['INDUSTRY', 'SECTOR']
        }

        # Find actual column names
        actual_columns = {}
        for our_name, possible_names in column_mapping.items():
            for possible in possible_names:
                if possible in df.columns:
                    actual_columns[our_name] = possible
                    break

        print(f"Mapped columns: {actual_columns}")  # Debug: see mapped columns

        # Check if we have at least symbol and some price column
        if 'SYMBOL' not in actual_columns:
            raise ValueError("CSV file missing SYMBOL column")

        if 'LTP' not in actual_columns and 'PREVIOUS CLOSE' not in actual_columns:
            raise ValueError("CSV file missing both LTP and PREVIOUS CLOSE columns")

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for _, row in df.iterrows():
            try:
                # Get symbol
                symbol_col = actual_columns['SYMBOL']
                symbol = str(row[symbol_col]).strip()

                if not symbol or symbol == 'nan' or symbol == 'None' or symbol == 'Symbol':
                    skipped_count += 1
                    continue

                # Get price - try LTP first, then previous close
                current_price = None
                if 'LTP' in actual_columns:
                    try:
                        current_price = float(row[actual_columns['LTP']])
                    except (ValueError, TypeError):
                        pass

                if current_price is None and 'PREVIOUS CLOSE' in actual_columns:
                    try:
                        current_price = float(row[actual_columns['PREVIOUS CLOSE']])
                    except (ValueError, TypeError):
                        pass

                if current_price is None or current_price <= 0:
                    skipped_count += 1
                    continue

                # Get company name
                company_name = symbol  # default to symbol
                if 'COMPANY NAME' in actual_columns:
                    try:
                        company_name = str(row[actual_columns['COMPANY NAME']]).strip()
                        if not company_name or company_name == 'nan':
                            company_name = symbol
                    except:
                        company_name = symbol

                # Get sector
                sector = None
                if 'INDUSTRY' in actual_columns:
                    try:
                        sector = str(row[actual_columns['INDUSTRY']]).strip()
                        if not sector or sector == 'nan':
                            sector = None
                    except:
                        sector = None

                # Create or update stock
                stock, created = Stock.objects.get_or_create(
                    symbol=symbol,
                    defaults={
                        'name': company_name,
                        'current_price': Decimal(str(current_price)),
                        'sector': sector,
                        'exchange': 'NSE'
                    }
                )

                if created:
                    created_count += 1
                    print(f"Created: {symbol} - {company_name} - {current_price}")
                else:
                    # Update existing stock - only update price if it's significantly different
                    price_changed = abs(float(stock.current_price) - current_price) > 0.01
                    name_changed = stock.name != company_name
                    sector_changed = stock.sector != sector

                    if price_changed or name_changed or sector_changed:
                        if price_changed:
                            stock.current_price = Decimal(str(current_price))
                        if name_changed:
                            stock.name = company_name
                        if sector_changed:
                            stock.sector = sector

                        stock.save()
                        updated_count += 1
                        print(f"Updated: {symbol} - Price: {stock.current_price} -> {current_price}")

            except Exception as e:
                print(f"Error processing row for symbol {symbol if 'symbol' in locals() else 'unknown'}: {str(e)}")
                skipped_count += 1
                continue

        print(f"Processed CSV: {created_count} created, {updated_count} updated, {skipped_count} skipped")
        return created_count, updated_count

    except Exception as e:
        print(f"Error processing CSV: {str(e)}")
        raise Exception(f"Error processing CSV: {str(e)}")

# Helper functions for data extraction
def get_numeric_value(row, column_name):
    """Safely extract numeric value from DataFrame row"""
    try:
        value = row.get(column_name)
        if pd.isna(value) or value is None:
            return None
        return float(value)
    except (ValueError, TypeError):
        return None


def get_string_value(row, column_name):
    """Safely extract string value from DataFrame row"""
    try:
        value = row.get(column_name)
        if pd.isna(value) or value is None:
            return None
        return str(value).strip()
    except (ValueError, TypeError):
        return None


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
                created_count, updated_count = process_nse_csv(save_path)
                messages.success(request, f"Updated stocks: {created_count} created, {updated_count} updated")
            except Exception as e:
                messages.error(request, f"Failed to process CSV: {str(e)}")
        else:
            messages.error(request, f"Failed to download {index_name} data")

        return redirect('trading:data_download')

    context = {
        'downloaded_files': downloaded_files
    }
    return render(request, 'trading/data_download.html', context)


@login_required
def trade_stock(request, stock_id=None):
    portfolio = get_object_or_404(Portfolio, user=request.user)
    if request.method == 'POST':
        form = TradeForm(request.POST)
        if form.is_valid():
            stock = form.cleaned_data['stock']
            transaction_type = form.cleaned_data['transaction_type']
            quantity = form.cleaned_data['quantity']
            notes = form.cleaned_data['notes']

            total_cost = stock.current_price * quantity
            if transaction_type == 'BUY':
                if portfolio.cash_balance < total_cost:
                    messages.error(request, "Insufficient funds for this purchase")
                    return redirect('trading:trade')
                portfolio.cash_balance -= total_cost
            else:  # SELL
                holding = Holding.objects.filter(portfolio=portfolio, stock=stock).first()
                if not holding or holding.quantity < quantity:
                    messages.error(request, "Insufficient shares to sell")
                    return redirect('trading:trade')
                portfolio.cash_balance += total_cost

            holding, created = Holding.objects.get_or_create(
                portfolio=portfolio,
                stock=stock,
                defaults={'quantity': 0, 'average_buy_price': stock.current_price}
            )
            if transaction_type == 'BUY':
                if holding.quantity > 0:
                    holding.average_buy_price = (
                            (holding.average_buy_price * holding.quantity + total_cost) /
                            (holding.quantity + quantity)
                    )
                holding.quantity += quantity
            else:  # SELL
                holding.quantity -= quantity
                if holding.quantity == 0:
                    holding.delete()
                else:
                    holding.save()

            portfolio.save()
            if holding.quantity > 0:
                holding.save()

            Transaction.objects.create(
                portfolio=portfolio,
                stock=stock,
                transaction_type=transaction_type,
                quantity=quantity,
                price_per_share=stock.current_price,
                notes=notes
            )
            messages.success(request, f"Successfully {transaction_type.lower()}ed {quantity} shares of {stock.symbol}")
            return redirect('trading:dashboard')
    else:
        form = TradeForm()
        # Debug: Check available stocks
        print(f"Stocks available in TradeForm: {Stock.objects.count()}")
        if Stock.objects.count() == 0:
            messages.warning(request, "No stocks available. Please ask an admin to download NSE data.")

    context = {
        'form': form,
        'portfolio': portfolio
    }
    return render(request, 'trading/trade.html', context)