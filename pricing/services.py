"""
Price calculation. No views and no templates here: the same function is used
by the calculator and (later) by the deals app.

adjusted price = base price x prime time index x channel split index
monthly price  = adjusted price x monthly coefficient
average price  = average of the 12 monthly prices (the only rounded value)
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

from pricing.exceptions import (
    InvalidPercentError,
    MissingCoefficientError,
    MissingPriceError,
)
from pricing.models import (
    IndexBand,
    Month,
    MonthlyCoefficient,
    PriceIndexType,
    TargetGroupPrice,
)

CENT = Decimal('0.01')


@dataclass(frozen=True)
class MonthlyPrice:
    month: int
    month_name: str
    coefficient: Decimal
    price: Decimal


@dataclass(frozen=True)
class PriceBreakdown:
    pricing_year: object
    target_group: object
    pt_percent: Decimal
    main_channel_percent: Decimal
    base_price: Decimal
    pt_index: Decimal
    channel_split_index: Decimal
    adjusted_price: Decimal
    months: tuple
    average_price: Decimal


def _to_percent(name, value):
    percent = Decimal(str(value))
    if not Decimal('0') <= percent <= Decimal('100'):
        raise InvalidPercentError(name, percent)
    return percent


def calculate(pricing_year, target_group, pt_percent, main_channel_percent):
    """Return a PriceBreakdown or raise PricingError (or a subclass)."""
    pt_percent = _to_percent('Prime time percent', pt_percent)
    main_channel_percent = _to_percent('Main channel percent', main_channel_percent)

    try:
        base_price = TargetGroupPrice.objects.get(
            pricing_year=pricing_year,
            target_group=target_group,
        ).base_price
    except TargetGroupPrice.DoesNotExist:
        raise MissingPriceError(pricing_year, target_group) from None

    pt_index = IndexBand.get_coefficient(pricing_year, PriceIndexType.PT, pt_percent)
    split_index = IndexBand.get_coefficient(
        pricing_year, PriceIndexType.CHANNEL_SPLIT, main_channel_percent
    )
    adjusted_price = base_price * pt_index * split_index

    coefficients = dict(
        MonthlyCoefficient.objects
        .filter(pricing_year=pricing_year)
        .values_list('month', 'coefficient')
    )

    months = []
    for number, label in Month.choices:
        if number not in coefficients:
            raise MissingCoefficientError(pricing_year, label)
        coefficient = coefficients[number]
        months.append(MonthlyPrice(
            month=number,
            month_name=label,
            coefficient=coefficient,
            price=adjusted_price * coefficient,
        ))

    average_price = (
        sum((row.price for row in months), Decimal('0')) / len(months)
    ).quantize(CENT, rounding=ROUND_HALF_UP)

    return PriceBreakdown(
        pricing_year=pricing_year,
        target_group=target_group,
        pt_percent=pt_percent,
        main_channel_percent=main_channel_percent,
        base_price=base_price,
        pt_index=pt_index,
        channel_split_index=split_index,
        adjusted_price=adjusted_price,
        months=tuple(months),
        average_price=average_price,
    )
