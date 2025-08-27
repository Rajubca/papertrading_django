# trading/templatetags/custom_filters.py
from django import template
from decimal import Decimal

register = template.Library()


@register.filter
def abs_value(value):
    """Return absolute value of a number"""
    try:
        return abs(value)
    except (TypeError, ValueError):
        return value


@register.filter
def abs_decimal(value):
    """Return absolute value for Decimal fields"""
    if isinstance(value, Decimal):
        return abs(value)
    try:
        return abs(float(value))
    except (TypeError, ValueError):
        return value
