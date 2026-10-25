from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.core.validators import MaxValueValidator, MinLengthValidator, MinValueValidator

from decimal import Decimal

from pricing.exceptions import IndexBandNotFound

# Helping classes
class Month(models.IntegerChoices):
    JAN = 1, 'Jan'
    FEB = 2, 'Feb'
    MAR = 3, 'Mar'
    APR = 4, 'Apr'
    MAY = 5, 'May'
    JUN = 6, 'Jun'
    JUL = 7, 'Jul'
    AUG = 8, 'Aug'
    SEP = 9, 'Sep'
    OCT = 10, 'Oct'
    NOV = 11, 'Nov'
    DEC = 12, 'Dec'

class PriceIndexType(models.TextChoices):
    PT = 'PT', 'Prime time'
    CHANNEL_SPLIT = 'CHANNEL_SPLIT', 'Channel split'


# Models
class PricingYear(models.Model):
    year = models.PositiveSmallIntegerField(
        unique=True,
        validators=[MinValueValidator(2000), MaxValueValidator(2100)],
    )

    class Meta:
        ordering = ['-year']

    def __str__(self):
        return str(self.year)


class Channel(models.Model):
    name = models.CharField(
        max_length=100,
        unique=True,
        validators=[MinLengthValidator(2)],
    )

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                Lower('name'),
                name='unique_channel_name_ci',
                violation_error_message='Channel with this name exists.',
            ),]

    def __str__(self):
        return self.name


class TargetGroup(models.Model):
    name = models.CharField(
        max_length=30,
        unique=True,
    )

    channels = models.ManyToManyField(
        Channel,
        related_name='target_groups',
    )

    class Meta:
        ordering = ['name']
        constraints = [
            models.UniqueConstraint(
                Lower('name'),
                name='unique_target_group_name_ci',
                violation_error_message='Target group with this name exists.',
            ),]

    def __str__(self):
        return self.name


class TargetGroupPrice(models.Model):
    pricing_year = models.ForeignKey(
        PricingYear,
        on_delete=models.PROTECT,
        related_name='group_prices',
     )
    target_group = models.ForeignKey(
        TargetGroup,
        on_delete=models.PROTECT,
        related_name='prices',
    )
    base_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )

    class Meta:
        ordering = ['-pricing_year__year', 'target_group__name']
        constraints = [
            models.UniqueConstraint(
                fields=['pricing_year', 'target_group'],
                name='unique_price_per_group_per_year',
                violation_error_message='This target group already has a price for the selected year.',
            ),]

    def __str__(self):
        return f'{self.target_group} / {self.pricing_year}: {self.base_price}'


class MonthlyCoefficient(models.Model):
    pricing_year = models.ForeignKey(
        PricingYear,
        on_delete=models.PROTECT,
        related_name='monthly_coefficients',
    )
    month = models.PositiveSmallIntegerField(
        choices=Month.choices,
    )
    coefficient = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[
            MinValueValidator('0.80'),
            MaxValueValidator('2.50')
        ],
    )

    class Meta:
        ordering = ['-pricing_year__year', 'month']
        constraints = [
            models.UniqueConstraint(
                fields=['pricing_year', 'month'],
                name='unique_coefficient_per_year_and_month',
                violation_error_message='Coefficient already exists for the selected month and year.',
            ),
        ]

    def __str__(self):
        return f'{self.pricing_year} / {self.get_month_display()}: {self.coefficient}'


class IndexBandQuerySet(models.QuerySet):
    def for_percent(self, pricing_year, index_type, percent) -> 'IndexBand':
        """ Returns the range with the smallest upper_limit >= percent or raises IndexBandNotFound."""
        band = (
            self.filter(
                pricing_year=pricing_year,
                index_type=index_type,
                upper_limit__gte=percent,
            )
            .order_by('upper_limit')
            .first()
        )
        if band is None:
            raise IndexBandNotFound(pricing_year, index_type, percent)
        return band

class IndexBand(models.Model):
    pricing_year = models.ForeignKey(
        PricingYear,
        on_delete=models.PROTECT,
        related_name='index_bands',
    )
    index_type = models.CharField(
        max_length=20,
        choices=PriceIndexType.choices,
    )
    upper_limit = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0')),
            MaxValueValidator(Decimal('100')),
        ],
        help_text='Up to and including this percent.',
    )
    coefficient = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
    )

    objects = IndexBandQuerySet.as_manager()

    class Meta:
        ordering = ['-pricing_year__year', 'index_type', 'upper_limit']
        constraints = [
            models.UniqueConstraint(
                fields=['pricing_year', 'index_type', 'upper_limit'],
                name='unique_index_band_per_year_type_limit',
                violation_error_message='A band with this upper limit already exists.',
            ),
            models.CheckConstraint(
                condition=Q(upper_limit__gte=0) & Q(upper_limit__lte=100),
                name='index_band_upper_limit_0_100',
            ),
        ]

    def __str__(self):
        return (
            f'{self.pricing_year} / {self.get_index_type_display()}: '
            f'up to {self.upper_limit}% → {self.coefficient}'
        )

    @classmethod
    def get_coefficient(cls, pricing_year, index_type, percent):
        return cls.objects.for_percent(pricing_year, index_type, percent).coefficient