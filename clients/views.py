from django.db.models import ProtectedError, Count
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView

from clients.models import Sector, Client
from clients.forms import ClientCreateForm, ClientEditForm, ClientDeleteForm, SectorCreateForm, SectorEditForm, SectorDeleteForm
from general.mixins import GetFormInstanceMixin

# ----------------------------------------------------- Sector Views
class SectorHomeListView(ListView):
    model = Sector
    paginate_by = 25
    template_name = 'sectors/sectors.html'
    context_object_name = "sectors"

    def get_queryset(self):
        queryset = super().get_queryset().annotate(client_count=Count('clients')).order_by('name')
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(name__icontains=query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '').strip()
        return context

class SectorCreateView(SuccessMessageMixin, CreateView):
    model = Sector
    form_class = SectorCreateForm
    success_url = reverse_lazy('clients:sector-list')
    template_name = 'sectors/sector_create.html'
    success_message = 'Sector "%(name)s" was created successfully.'

class SectorEditView(SuccessMessageMixin, UpdateView):
    model = Sector
    form_class = SectorEditForm
    success_url = reverse_lazy('clients:sector-list')
    template_name = 'sectors/sector_edit.html'
    success_message = 'Sector "%(name)s" was edited successfully.'

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
        messages.success(self.request, f'Sector "{self.object.name}" was deleted successfully.')
        return HttpResponseRedirect(self.get_success_url())

class SectorDetailView(DetailView):
    model = Sector
    template_name = 'sectors/sector_detail.html'


# ----------------------------------------------------- Client Views
class ClientHomeListView(ListView):
    model = Client
    paginate_by = 10
    template_name = 'clients/clients.html'
    context_object_name = "clients"

    def get_queryset(self):
        queryset = super().get_queryset().select_related('sector')
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(name__icontains=query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '').strip()
        return context


class ClientCreateView(SuccessMessageMixin, CreateView):
    model = Client
    form_class = ClientCreateForm
    success_url = reverse_lazy('clients:client-list')
    template_name = 'clients/client_create.html'
    success_message = 'Client "%(name)s" was created successfully.'

class ClientEditView(SuccessMessageMixin, UpdateView):
    model = Client
    form_class = ClientEditForm
    success_url = reverse_lazy('clients:client-list')
    template_name = 'clients/client_edit.html'
    success_message = 'Client "%(name)s" was edited successfully.'

class ClientDeleteView(SuccessMessageMixin, GetFormInstanceMixin, DeleteView):
    model = Client
    form_class = ClientDeleteForm
    success_url = reverse_lazy('clients:client-list')
    template_name = 'clients/client_delete.html'
    success_message = 'Client "%(name)s" was deleted successfully.'

class ClientDetailView(DetailView):
    model = Client
    template_name = 'clients/client_detail.html'
