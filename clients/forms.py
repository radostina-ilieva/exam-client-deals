from django import forms
from django.core.exceptions import ValidationError

from clients.models import Sector, Client
from general.mixins import DisableFieldsMixin


# ----------------------------------------------------- Sector Forms
class SectorBaseForm(forms.ModelForm):
    class Meta:
        model = Sector
        fields = ['name',]
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Sector name',
                'class': 'form-control'})
        }
        labels = {
            'name': 'Sector name',
        }
        help_texts = {
            'name': f'Enter a unique sector name with length between 2-100 characters.',
        }
        error_messages = {
            'name': {
                'required': 'Please enter a sector name.',
                'max_length': 'The sector name cannot be longer than 100 characters.',
                'unique': 'A sector with this name already exists.',
            },
        }

    def clean_name(self):
        name = self.cleaned_data['name']

        duplicates = Sector.objects.filter(name__iexact=name)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)

        if duplicates.exists():
            raise ValidationError('A sector with this name already exists.')

        return name


class SectorCreateForm(SectorBaseForm):
    ...

class SectorEditForm(SectorBaseForm):
    ...

class SectorDeleteForm(DisableFieldsMixin, SectorBaseForm):
    ...

# ----------------------------------------------------- Client Forms
class ClientBaseForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'sector',]
        widgets = {
            'name': forms.TextInput(attrs={
                'placeholder': 'Client name',
                'class': 'form-control'}),
            'sector': forms.Select(attrs={'class': 'form-select'}),
        }
        labels = {
            'name': 'Client name',
            'sector': 'Sector',
        }
        help_texts = {
            'name': f'Enter a unique client name with length between 2-100 characters.',
            'sector': 'Choose a sector.',
        }
        error_messages = {
            'name': {
                'required': 'Please enter a client name.',
                'max_length': 'The client name cannot be longer than 100 characters.',
                'unique': 'A client with this name already exists.',
            },
            'sector': {
                'required': 'Please select a sector.',
                'invalid_choice': 'The selected sector is not valid.',
            },
        }


    def clean_name(self):
        name = self.cleaned_data['name']

        duplicates = Client.objects.filter(name__iexact=name)
        if self.instance.pk:
            duplicates = duplicates.exclude(pk=self.instance.pk)

        if duplicates.exists():
            raise ValidationError('A client with this name already exists.')

        return name


class ClientCreateForm(ClientBaseForm):
    ...

class ClientEditForm(ClientBaseForm):
    ...

class ClientDeleteForm(DisableFieldsMixin, ClientBaseForm):
    ...

