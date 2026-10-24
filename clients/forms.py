from django import forms
from clients.models import Sector, Client
from general.mixins import DisableFieldsMixin

class SectorBaseForm(forms.ModelForm):
    class Meta:
        model = Sector
        fields = ['name',]
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Sector name'})
        }

class SectorCreateForm(SectorBaseForm):
    ...

class SectorEditForm(SectorBaseForm):
    ...

class SectorDeleteForm(DisableFieldsMixin, SectorBaseForm):
    ...


class ClientBaseForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ['name', 'sector',]
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Client name'})
        }

class ClientCreateForm(ClientBaseForm):
    ...

class ClientEditForm(ClientBaseForm):
    ...

class ClientDeleteForm(DisableFieldsMixin, ClientBaseForm):
    ...

