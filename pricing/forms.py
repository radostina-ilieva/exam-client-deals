from decimal import Decimal

from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

from general.mixins import DisableFieldsMixin
from pricing.models import (
    MAX_MONTHLY_COEFFICIENT, MIN_MONTHLY_COEFFICIENT, Channel, IndexBand, Month, MonthlyCoefficient,
    PricingYear, TargetGroup, TargetGroupPrice,
)


class BootstrapCheckboxSelectMultiple(forms.CheckboxSelectMultiple):
    """Bootstrap classes only on the inputs, not on the wrapping <div>."""

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['attrs'].pop('class', None)  # wrapper <div>: no class
        return context

    def create_option(self, *args, **kwargs):
        option = super().create_option(*args, **kwargs)
        option['attrs']['class'] = 'form-check-input me-2'
        return option

# ----------------------------------------------------- Year Forms
class PricingYearForm(forms.ModelForm):
    class Meta:
        model = PricingYear
        fields = ['year']
        widgets = {
            'year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 2027',
                'min': 2000,
                'max': 2100,
            }),
        }
        labels = {'year': 'Year'}
        help_texts = {'year': 'A year can be between 2000 and 2100. Every year can be created only once.'}
        error_messages = {
            'year': {
                'required': 'Please enter a year.',
                'invalid': 'Enter a whole number.',
                'unique': 'This year already exists.',
                'min_value': 'The year cannot be earlier than 2000.',
                'max_value': 'The year cannot be later than 2100.',
            },
        }


class PricingYearDeleteForm(DisableFieldsMixin, PricingYearForm):
    ...

# ----------------------------------------------------- Channel Forms
class ChannelForm(forms.ModelForm):
    class Meta:
        model = Channel
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Channel name',
            }),
        }
        labels = {'name': 'Channel name'}
        help_texts = {'name': 'A unique channel name with length between 2-100 characters.'}
        error_messages = {
            'name': {
                'required': 'Please enter a channel name.',
                'max_length': 'The channel name cannot be longer than 100 characters.',
                'unique': 'A channel with this name already exists.',
            },
        }

    def clean_name(self):
        name = self.cleaned_data['name']

        duplicates = Channel.objects.filter(name__iexact=name)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)

        if duplicates.exists():
            raise ValidationError('A channel with this name already exists.')

        return name


class ChannelDeleteForm(DisableFieldsMixin, ChannelForm):
    ...


# ----------------------------------------------------- Target Group Forms
class TargetGroupForm(forms.ModelForm):
    class Meta:
        model = TargetGroup
        fields = ['name', 'channels']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. A18-49',
            }),
            'channels': BootstrapCheckboxSelectMultiple(),
        }
        labels = {
            'name': 'Target group name',
            'channels': 'Channels',
        }
        help_texts = {
            'name': 'A unique name, up to 30 characters.',
            'channels': 'Select at least one channel.',
        }
        error_messages = {
            'name': {
                'required': 'Please enter a target group name.',
                'max_length': 'The target group name cannot be longer than 30 characters.',
                'unique': 'A target group with this name already exists.',
            },
            'channels': {
                'required': 'Please select at least one channel.',
                'invalid_choice': 'One of the selected channels is not valid.',
            },
        }

    def clean_name(self):
        name = self.cleaned_data['name']

        duplicates = TargetGroup.objects.filter(name__iexact=name)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)

        if duplicates.exists():
            raise ValidationError('A target group with this name already exists.')

        return name

    def clean_channels(self):
        channels = self.cleaned_data['channels']
        if not channels:
            raise ValidationError('Please select at least one channel.')
        return channels


class TargetGroupDeleteForm(DisableFieldsMixin, TargetGroupForm):
    ...


# ----------------------------------------------------- Target Group Price Forms
class TargetGroupPriceForm(forms.ModelForm):
    class Meta:
        model = TargetGroupPrice
        fields = ['pricing_year', 'target_group', 'base_price']
        widgets = {
            'pricing_year': forms.Select(attrs={'class': 'form-select'}),
            'target_group': forms.Select(attrs={'class': 'form-select'}),
            'base_price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 285.00',
                'step': '0.01',
                'min': '0.01',
            }),
        }
        labels = {
            'pricing_year': 'Pricing year',
            'target_group': 'Target group',
            'base_price': 'Base price',
        }
        help_texts = {
            'pricing_year': 'Choose a year.',
            'target_group': 'Choose a target group.',
            'base_price': 'A positive value with up to 2 decimal places.',
        }
        error_messages = {
            'pricing_year': {
                'required': 'Please select a year.',
                'invalid_choice': 'The selected year is not valid.',
            },
            'target_group': {
                'required': 'Please select a target group.',
                'invalid_choice': 'The selected target group is not valid.',
            },
            'base_price': {
                'required': 'Please enter a base price.',
                'invalid': 'Enter a valid amount.',
                'min_value': 'The base price must be at least 0.01.',
                'max_digits': 'The base price must be max 999999.99.',
                'max_decimal_places': 'Use at most 2 decimal places.',
            },
        }


class TargetGroupPriceEditForm(TargetGroupPriceForm):
    """Year and target group are locked, only the price can change."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['pricing_year'].disabled = True
        self.fields['target_group'].disabled = True


class TargetGroupPriceDeleteForm(DisableFieldsMixin, TargetGroupPriceForm):
    ...

# ----------------------------------------------------- Monthly Coefficients Form
class MonthlyCoefficientsForm(forms.Form):
    """12 fields (month_1 ... month_12) created in a loop, one per month."""

    def __init__(self, *args, pricing_year, **kwargs):
        super().__init__(*args, **kwargs)
        self.pricing_year = pricing_year

        saved = dict(
            MonthlyCoefficient.objects
            .filter(pricing_year=pricing_year)
            .values_list('month', 'coefficient')
        )

        for number, label in Month.choices:
            self.fields[self.field_name(number)] = forms.DecimalField(
                label=label,
                min_value=MIN_MONTHLY_COEFFICIENT,
                max_value=MAX_MONTHLY_COEFFICIENT,
                max_digits=3,
                decimal_places=2,
                initial=saved.get(number),
                widget=forms.NumberInput(attrs={
                    'class': 'form-control',
                    'step': '0.01',
                    'min': str(MIN_MONTHLY_COEFFICIENT),
                    'max': str(MAX_MONTHLY_COEFFICIENT),
                    'placeholder': '1.00',
                }),
                error_messages={
                    'required': f'Enter a coefficient for {label}.',
                    'invalid': 'Enter a valid number.',
                    'min_value': f'The coefficient cannot be below {MIN_MONTHLY_COEFFICIENT}.',
                    'max_value': f'The coefficient cannot be above {MAX_MONTHLY_COEFFICIENT}.',
                    'max_digits': 'Use the format 1.25.',
                    'max_decimal_places': 'Use at most 2 decimal places.',
                },
            )

    @staticmethod
    def field_name(month_number):
        return f'month_{month_number}'

    def save(self):
        """Create or update all 12 rows, all or nothing."""
        with transaction.atomic():
            for number, _label in Month.choices:
                MonthlyCoefficient.objects.update_or_create(
                    pricing_year=self.pricing_year,
                    month=number,
                    defaults={'coefficient': self.cleaned_data[self.field_name(number)]},
                )

# ----------------------------------------------------- Index Bands Forms
class IndexBandForm(forms.ModelForm):
    class Meta:
        model = IndexBand
        fields = ['pricing_year', 'index_type', 'upper_limit', 'coefficient']
        widgets = {
            'pricing_year': forms.Select(attrs={'class': 'form-select'}),
            'index_type': forms.Select(attrs={'class': 'form-select'}),
            'upper_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 55',
                'step': '0.01',
                'min': 0,
                'max': 100,
            }),
            'coefficient': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g. 1.05',
                'step': '0.01',
                'min': '0.01',
            }),
        }
        labels = {
            'pricing_year': 'Pricing year',
            'index_type': 'Index type',
            'upper_limit': 'Up to (%)',
            'coefficient': 'Index coefficient',
        }
        help_texts = {
            'pricing_year': 'Choose a year.',
            'index_type': 'Prime time or channel split.',
            'upper_limit': 'The band applies up to and including this percent (0-100). '
                           'Add a band with 100 to cover the whole range.',
            'coefficient': 'The multiplier for this band, for example 1.05.',
        }
        error_messages = {
            'pricing_year': {'required': 'Please select a year.'},
            'index_type': {'required': 'Please select an index type.'},
            'upper_limit': {
                'required': 'Please enter the upper limit.',
                'invalid': 'Enter a valid number.',
                'min_value': 'The upper limit cannot be below 0.',
                'max_value': 'The upper limit cannot be above 100.',
            },
            'coefficient': {
                'required': 'Please enter the coefficient.',
                'invalid': 'Enter a valid number.',
                'min_value': 'The coefficient must be at least 0.01.',
                'max_digits': 'Use the format 1.05.',
            },
        }


class IndexBandDeleteForm(DisableFieldsMixin, IndexBandForm):
    ...

# ----------------------------------------------------- Calculator Form
class PriceCalculatorForm(forms.Form):
    pricing_year = forms.ModelChoiceField(
        queryset=PricingYear.objects.all(),
        label='Pricing year',
        empty_label='Select a year',
        widget=forms.Select(attrs={'class': 'form-select'}),
        error_messages={
            'required': 'Please select a year.',
            'invalid_choice': 'The selected year is not valid.',
        },
    )
    target_group = forms.ModelChoiceField(
        queryset=TargetGroup.objects.all(),
        label='Target group',
        empty_label='Select a target group',
        widget=forms.Select(attrs={'class': 'form-select'}),
        error_messages={
            'required': 'Please select a target group.',
            'invalid_choice': 'The selected target group is not valid.',
        },
    )
    pt_percent = forms.DecimalField(
        label='Prime time (%)',
        initial=55,
        min_value=Decimal('0'),
        max_value=Decimal('100'),
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100,
        }),
        error_messages={
            'required': 'Please enter the prime time share.',
            'invalid': 'Enter a valid number.',
            'min_value': 'The Prime time (%) cannot be below 0.',
            'max_value': 'The Prime time (%) cannot be above 100.',
        },
    )
    main_channel_percent = forms.DecimalField(
        label='Channel split bTV/TC (%)',
        initial=70,
        min_value=Decimal('0'),
        max_value=Decimal('100'),
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 'step': '0.01', 'min': 0, 'max': 100,
        }),
        error_messages={
            'required': 'Please enter the main channel share.',
            'invalid': 'Enter a valid number.',
            'min_value': 'The Channel split (%) cannot be below 0.',
            'max_value': 'The Channel split (%) cannot be above 100.',
        },
    )

    def clean(self):
        cleaned_data = super().clean()
        year = cleaned_data.get('pricing_year')
        group = cleaned_data.get('target_group')

        if year and group and not TargetGroupPrice.objects.filter(
            pricing_year=year, target_group=group
        ).exists():
            raise ValidationError(
                f'Target group "{group}" has no base price for {year}. '
                'Add the price first.'
            )

        return cleaned_data
