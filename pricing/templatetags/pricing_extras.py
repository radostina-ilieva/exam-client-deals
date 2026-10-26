from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from django import template
from pricing.models import Month

register = template.Library()


def _to_decimal(value):
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


@register.filter
def percent(value):
    """55 -> '55%', Decimal('55.50') -> '55.5%'."""
    number = _to_decimal(value)
    if number is None:
        return value
    return f'{format(number.normalize(), "f")}%'


@register.filter
def money(value):
    """Decimal('1234.5') -> '1,234.50'."""
    number = _to_decimal(value)
    if number is None:
        return value
    return f'{number.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP):,.2f}'


@register.simple_tag
def month_name(number):
    """1 -> 'Jan'."""
    try:
        return Month(int(number)).label
    except (ValueError, TypeError):
        return ''
