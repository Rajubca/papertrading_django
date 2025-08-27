from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

app_name = 'trading'

urlpatterns = [
    # Dashboard (both root and /dashboard/ point to same view)
    path('', views.dashboard, name='dashboard1'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Admin management
    path('admin/portfolio-visibility/', views.manage_portfolio_visibility, name='admin_portfolio_visibility'),
    path('ajax/calc-order/', views.calculate_order, name='calculate_order'),
    #Staff
    path('admin/portfolio-manager/', views.portfolio_manager, name='portfolio_manager'),
    path('admin/portfolio/bulk-update/', views.bulk_update_visibility, name='bulk_update_visibility'),
    path('admin/portfolio/<int:portfolio_id>/toggle-visibility/', views.toggle_portfolio_visibility, name='toggle_portfolio_visibility'),
    # Portfolios
    path('portfolios/', views.portfolio_list, name='portfolio_list'),
    path('portfolios/create/', views.create_portfolio, name='create_portfolio'),
    path('portfolios/manage/', views.portfolio_list, name='portfolio_manage'),
    path('portfolios/<int:pk>/delete/', views.delete_portfolio, name='portfolio_delete'),

    # Stocks
    path('stocks/', views.stock_list, name='stock_list'),
    path('stocks/<int:pk>/', views.stock_detail, name='stock_detail'),
    path('stocks/<int:pk>/update-price/', views.update_stock_price, name='update_stock_price'),
    path('stock-search/', views.stock_search, name='stock_search'),

    # Trading
    path('trade/', views.trade_stock, name='trade'),
    path('trade/<int:stock_id>/', views.trade_stock, name='trade_stock'),
    # trading/urls.py calculate order
    path('ajax/calc-order/', views.calculate_order_summary, name='calculate_order'),


    # Transactions
    path('transactions/', views.transaction_list, name='transaction_list'),
    # Add this URL pattern to your urlpatterns list
    path('transactions/history/', views.transaction_list, name='transaction_history'),

    # Reports
    # #     path('reports/', views.reports, name='reports'),
    #     path('reports/<int:pk>/', views.report_detail, name='report_detail'),
          # Reports
          # 
    path('reports/', views.reports, name='reports'),
    path('reports/generate/', views.generate_report, name='generate_report'),
    path('reports/<int:portfolio_id>/<int:pk>/', views.report_detail, name='report_detail'),
    # path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    path('reports/delete/<int:pk>/', views.delete_report, name='delete_report'),

    # Watchlists
    path('watchlists/', views.watchlists, name='watchlists'),

    # Authentication (consolidated under accounts/)
    path('accounts/register/', views.register, name='register'),
    path('accounts/signup/', views.signup, name='signup'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(template_name='registration/logout.html'), name='logout'),
    path('accounts/profile/', views.profile, name='profile'),
    path('reports/', views.reports, name='reports'),
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    path('reports/generate/', views.generate_report, name='generate_report'),
    # Password reset
    path('accounts/password-reset/',
         auth_views.PasswordResetView.as_view(template_name='registration/password_reset.html'),
         name='password_reset'),
    path('accounts/password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),
    path('accounts/password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('accounts/password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),

    # for stocks of F&O nse downloads
    path('download-data/', views.download_nse_data, name='data_download'),
    path('view-file/<str:filename>/', views.view_file, name='view_file'),

    path('api/stock-price/<int:stock_id>/', views.get_stock_price_api, name='stock_price_api'),
    path('api/stock-transactions/<int:stock_id>/', views.stock_transactions_api, name='stock_transactions_api'),
    path('reports/<int:pk>/', views.report_detail, name='report_detail'),
    path('reports/generate/', views.generate_report, name='generate_report'),
]
