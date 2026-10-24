from django.db.models import ProtectedError
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from clients.models import Sector, Client
from clients.forms import ClientCreateForm, ClientEditForm, ClientDeleteForm, SectorCreateForm, SectorEditForm, SectorDeleteForm
from general.mixins import GetFormInstanceMixin

class SectorHomeListView(ListView):
    model = Sector
    paginate_by = 20
    template_name = 'sectors/sectors.html'
    context_object_name = "sectors"

class SectorCreateView(CreateView):
    model = Sector
    form_class = SectorCreateForm
    success_url = reverse_lazy('clients:sector-list')
    template_name = 'sectors/sector_create.html'

class SectorEditView(UpdateView):
    model = Sector
    form_class = SectorEditForm
    template_name = 'sectors/sector_edit.html'
    def get_success_url(self) -> str:
        return reverse('clients:sector-detail', kwargs={'pk': self.object.pk})

class SectorDeleteView(GetFormInstanceMixin, DeleteView):
    model = Sector
    form_class = SectorDeleteForm
    success_url = reverse_lazy('clients:sector-list')
    template_name = 'sectors/sector_delete.html'
    def form_valid(self, form):
        try:
            self.object.delete()
        except ProtectedError:
            messages.error(
                self.request,
                f'Cannot delete sector "{self.object.name}" because it has clients. '
                'Reassign or delete them first.'
            )
            return redirect('clients:sector-list')
        return HttpResponseRedirect(self.get_success_url())

class SectorDetailView(DetailView):
    model = Sector
    template_name = 'sectors/sector_detail.html'

class ClientHomeListView(ListView):
    model = Client
    paginate_by = 50
    template_name = 'clients/clients.html'
    context_object_name = "clients"

class ClientCreateView(CreateView):
    model = Client
    form_class = ClientCreateForm
    success_url = reverse_lazy('clients:client-list')
    template_name = 'clients/client_create.html'

class ClientEditView(UpdateView):
    model = Client
    form_class = ClientEditForm
    template_name = 'clients/client_edit.html'
    def get_success_url(self) -> str:
        return reverse('clients:client-detail', kwargs={'pk': self.object.pk})

class ClientDeleteView(GetFormInstanceMixin, DeleteView):
    model = Client
    form_class = ClientDeleteForm
    success_url = reverse_lazy('clients:client-list')
    template_name = 'clients/client_delete.html'

class ClientDetailView(DetailView):
    model = Client
    template_name = 'clients/client_detail.html'
