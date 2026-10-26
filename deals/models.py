from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Q

from clients.models import Client
from pricing.models import PricingYear, TargetGroup


class Offer(models.Model):

    class StatusChoices(models.TextChoices):
        DRAFT = 'Draft', 'Draft'
        SENT = 'Sent', 'Sent'
        ACCEPTED = 'Accepted', 'Accepted'
        REJECTED = 'Rejected', 'Rejected'

    client = models.ForeignKey(
        Client,
        on_delete=models.PROTECT,
        related_name='offers',
    )

    pricing_year = models.ForeignKey(
        PricingYear,
        on_delete=models.PROTECT,
        related_name='offers',
    )

    target_group = models.ForeignKey(
        TargetGroup,
        on_delete=models.PROTECT,
        related_name='offers',
    )

    pt_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    main_channel_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(0),
            MaxValueValidator(100),
        ],
    )

    # Snapshot of the calculated price
    base_price = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        editable=False,
    )

    pt_index = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        editable=False,
    )

    channel_split_index = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        editable=False,
    )

    adjusted_price = models.DecimalField(
        max_digits=16,
        decimal_places=6,
        editable=False,
    )

    average_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        editable=False,
    )

    status = models.CharField(
        max_length=10,
        choices=StatusChoices.choices,
        default=StatusChoices.DRAFT,
    )

    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-pk']
        constraints = [
            models.CheckConstraint(
                condition=Q(pt_percent__gte=0, pt_percent__lte=100),
                name='offer_pt_percent_0_100',
            ),
            models.CheckConstraint(
                condition=Q(
                    main_channel_percent__gte=0,
                    main_channel_percent__lte=100,
                ),
                name='offer_channel_percent_0_100',
            ),
        ]

    def apply_breakdown(self, breakdown):
        self.base_price = breakdown.base_price
        self.pt_index = breakdown.pt_index
        self.channel_split_index = breakdown.channel_split_index
        self.adjusted_price = breakdown.adjusted_price
        self.average_price = breakdown.average_price

    def __str__(self):
        return (
            f'Offer #{self.pk} - {self.client} '
            f'({self.pricing_year}, {self.target_group})'
        )