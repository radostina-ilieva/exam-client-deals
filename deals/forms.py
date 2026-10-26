from django import forms
from django.core.exceptions import ValidationError

from deals.models import Offer
from general.mixins import DisableFieldsMixin
from pricing.exceptions import PricingError
from pricing.services import calculate


# ----------------------------------------------------- Offer Forms
class OfferBaseForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = [
            'client',
            'pricing_year',
            'target_group',
            'pt_percent',
            'main_channel_percent',
            'status',
            'notes',
        ]
        widgets = {
            'client': forms.Select(attrs={'class': 'form-select'}),
            'pricing_year': forms.Select(attrs={'class': 'form-select'}),
            'target_group': forms.Select(attrs={'class': 'form-select'}),
            'pt_percent': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 0.01,
                'min': 0,
                'max': 100,
                'placeholder': 'e.g. 45.00',
            }),
            'main_channel_percent': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': 0.01,
                'min': 0,
                'max': 100,
                'placeholder': 'e.g. 60.00',
            }),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Optional notes about this offer',
            }),
        }
        labels = {
            'client': 'Client',
            'pricing_year': 'Pricing year',
            'target_group': 'Target group',
            'pt_percent': 'Prime time (%)',
            'main_channel_percent': 'Channel split bTV/TC (%)',
            'status': 'Status',
            'notes': 'Notes',
        }
        help_texts = {
            'client': 'Choose a client.',
            'pricing_year': (
                'Choose the pricing year. The offer keeps the price '
                'calculated at the moment of its creation.'
            ),
            'target_group': 'Choose the target group.',
            'pt_percent': 'Prime time (%), between 0 and 100.',
            'main_channel_percent': 'Channel split (%), between 0 and 100.',
            'status': 'Choose the current status of the offer.',
            'notes': 'Optional. Any additional information about the offer.',
        }
        error_messages = {
            'client': {
                'required': 'Please select a client.',
                'invalid_choice': 'The selected client is not valid.',
            },
            'pricing_year': {
                'required': 'Please select a pricing year.',
                'invalid_choice': 'The selected pricing year is not valid.',
            },
            'target_group': {
                'required': 'Please select a target group.',
                'invalid_choice': 'The selected target group is not valid.',
            },
            'pt_percent': {
                'required': 'Please enter the prime time percent.',
                'invalid': 'Enter a valid number.',
                'max_digits': 'The prime time percent is too long.',
                'max_decimal_places': 'Use no more than 2 decimal places.',
                'max_whole_digits': 'The prime time percent cannot be more than 100.',
            },
            'main_channel_percent': {
                'required': 'Please enter the channel split percent.',
                'invalid': 'Enter a valid number.',
                'max_digits': 'The channel split percent is too long.',
                'max_decimal_places': 'Use no more than 2 decimal places.',
                'max_whole_digits': 'The channel split percent cannot be more than 100.',
            },
            'status': {
                'required': 'Please select a status.',
                'invalid_choice': 'The selected status is not valid.',
            },
        }

    def clean_pt_percent(self):
        pt_percent = self.cleaned_data['pt_percent']

        if pt_percent < 0:
            raise ValidationError('The prime time percent cannot be less than 0.')
        if pt_percent > 100:
            raise ValidationError('The prime time percent cannot be more than 100.')

        return pt_percent

    def clean_main_channel_percent(self):
        main_channel_percent = self.cleaned_data['main_channel_percent']

        if main_channel_percent < 0:
            raise ValidationError('The channel split percent cannot be less than 0.')
        if main_channel_percent > 100:
            raise ValidationError('The channel split percent cannot be more than 100.')

        return main_channel_percent


class OfferForm(OfferBaseForm):
    """
    Create form. The price is calculated here, in clean(), because only
    clean() has all the fields at once (clean_<field> does not).
    """

    def clean(self):
        cleaned_data = super().clean()

        pricing_year = cleaned_data.get('pricing_year')
        target_group = cleaned_data.get('target_group')
        pt_percent = cleaned_data.get('pt_percent')
        main_channel_percent = cleaned_data.get('main_channel_percent')

        # A field with an error is missing from cleaned_data -> .get() is None.
        # Calculate only when all four values are valid.
        if None not in (
            pricing_year, target_group, pt_percent, main_channel_percent
        ):
            try:
                result = calculate(
                    pricing_year,
                    target_group,
                    pt_percent,
                    main_channel_percent,
                )
            except PricingError as error:
                raise ValidationError(str(error))

            # The snapshot fields are NOT NULL, so they must be set before save().
            self.instance.apply_breakdown(result)

        return cleaned_data


class OfferEditForm(OfferBaseForm):
    """
    Edit form. Only status and notes can change. It deliberately does not
    inherit OfferForm, otherwise clean() would recalculate the price and
    replace the saved snapshot.
    """
    LOCKED_FIELDS = (
        'client',
        'pricing_year',
        'target_group',
        'pt_percent',
        'main_channel_percent',
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name in self.LOCKED_FIELDS:
            self.fields[field_name].disabled = True


class OfferDeleteForm(DisableFieldsMixin, OfferBaseForm):
    ...
