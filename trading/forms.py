# forms.py
from django import forms

from .models import Portfolio
from .models import Watchlist, Holding


# In your forms.py file
# In your forms.py file


class PortfolioForm(forms.ModelForm):
    class Meta:
        model = Portfolio
        fields = ['name', 'cash_balance']  # Add other fields as needed


# trading/forms.py

from django import forms
from .models import Transaction, Portfolio, Stock

from django import forms
from .models import Transaction, Portfolio, Stock, Holding


class TradeForm(forms.ModelForm):
    portfolio = forms.ModelChoiceField(
        queryset=Portfolio.objects.none(),
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True,
        empty_label="Select Portfolio"
    )

    class Meta:
        model = Transaction
        fields = ['portfolio', 'stock', 'transaction_type', 'quantity', 'price_per_share', 'notes']
        widgets = {
            'stock': forms.Select(attrs={'class': 'form-control', 'id': 'id_stock'}),
            'transaction_type': forms.Select(attrs={'class': 'form-control', 'id': 'id_transaction_type'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'id': 'id_quantity', 'min': '1'}),
            'price_per_share': forms.NumberInput(
                attrs={'class': 'form-control', 'id': 'id_price_per_share', 'step': '0.01', 'min': '0.01'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'id': 'id_notes'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(TradeForm, self).__init__(*args, **kwargs)

        if user:
            # Filter portfolios to only those belonging to the user
            self.fields['portfolio'].queryset = Portfolio.objects.filter(
                user=user,
                visibility='PUBLIC'
            )

            # Set initial portfolio if only one exists
            portfolios = Portfolio.objects.filter(user=user, visibility='PUBLIC')
            if portfolios.count() == 1:
                self.fields['portfolio'].initial = portfolios.first()

    def clean(self):
        cleaned_data = super().clean()
        portfolio = cleaned_data.get('portfolio')
        transaction_type = cleaned_data.get('transaction_type')
        quantity = cleaned_data.get('quantity')
        stock = cleaned_data.get('stock')
        price_per_share = cleaned_data.get('price_per_share')
        notes = cleaned_data.get('notes')

        if not portfolio:
            raise forms.ValidationError("Please select a portfolio.")

        if quantity is not None and quantity <= 0:
            raise forms.ValidationError("Quantity must be greater than zero.")

        if price_per_share is not None and price_per_share <= 0:
            raise forms.ValidationError("Price per share must be greater than zero.")

        if transaction_type == 'BUY':
            total_cost = quantity * price_per_share
            if total_cost > portfolio.cash_balance:
                raise forms.ValidationError(
                    f"Insufficient funds. You need ₹{total_cost:.2f} but only have ₹{portfolio.cash_balance:.2f}."
                )

        return cleaned_data


class StockForm(forms.ModelForm):
    class Meta:
        model = Stock
        fields = ['symbol', 'name', 'current_price', 'sector', 'exchange']
        widgets = {
            'symbol': forms.TextInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'current_price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'sector': forms.TextInput(attrs={'class': 'form-control'}),
            'exchange': forms.TextInput(attrs={'class': 'form-control'}),
        }


class WatchlistForm(forms.ModelForm):
    class Meta:
        model = Watchlist
        fields = ['name', 'stocks']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'stocks': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }


# trading/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    phone = forms.CharField(max_length=20, required=False)
    birth_date = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'phone', 'birth_date']


class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone', 'birth_date']


class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=254)
    phone = forms.CharField(max_length=20)
    birth_date = forms.DateField(help_text='Required. Format: YYYY-MM-DD')

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'birth_date', 'password1', 'password2')
