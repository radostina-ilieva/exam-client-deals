from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import F
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from deals.models import Offer
from deals.forms import OfferForm, OfferEditForm, OfferDeleteForm
from pricing.models import PricingYear, TargetGroup
from general.mixins import FilterQueryMixin, GetFormInstanceMixin, ProtectedDeleteMixin


def _valid_pk(value):
    """Return an integer GET-filter value, or None for invalid/empty input."""
    return int(value) if value and value.isdigit() else None


class OfferListView(FilterQueryMixin, ListView):
    model = Offer
    paginate_by = 25
    template_name = 'deals/offers.html'
    context_object_name = 'offers'

    def get_queryset(self):
        queryset = (
            Offer.objects.select_related("client", "pricing_year", "target_group")
        )
        year_id = _valid_pk(self.request.GET.get("year"))
        group_id = _valid_pk(self.request.GET.get("group"))
        if year_id is not None:
            queryset = queryset.filter(pricing_year_id=year_id)
        if group_id is not None:
            queryset = queryset.filter(target_group_id=group_id)

        ordering_options = {
            "group": "target_group__name",
            "-group": "-target_group__name",
            "price": "average_price",
            "-price": "-average_price",
            "year": "pricing_year__year",
            "-year": "-pricing_year__year",
            "client": "client__name",
            "-client": "-client__name",
            "created": "created_at",
            "-created": "-created_at",
        }
        requested_ordering = self.request.GET.get("ordering", "")
        self.ordering = requested_ordering if requested_ordering in ordering_options else ""
        if self.ordering:
            queryset = queryset.order_by(ordering_options[self.ordering], "-pk")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year_id = _valid_pk(self.request.GET.get("year"))
        group_id = _valid_pk(self.request.GET.get("group"))
        context.update({
            "years": PricingYear.objects.all(),
            "groups": TargetGroup.objects.all(),
            "selected_year": year_id,
            "selected_group": group_id,
            "ordering": getattr(self, "ordering", ""),
        })
        return context

class OfferCreateView(SuccessMessageMixin, CreateView):
    model = Offer
    form_class = OfferForm
    template_name = 'deals/offer_create.html'
    success_url = reverse_lazy("deals:offer-list")
    success_message = "Offer for %(client)s was created successfully."

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["has_years"] = PricingYear.objects.exists()
        context["has_groups"] = TargetGroup.objects.exists()
        return context

    def get_success_message(self, cleaned_data):
        return self.success_message % {"client": self.object.client}


class OfferEditView(SuccessMessageMixin, UpdateView):
    model = Offer
    form_class = OfferEditForm
    template_name = 'deals/offer_edit.html'
    success_message = "Offer was edited successfully."

    def get_success_message(self, cleaned_data):
        return self.success_message

    def get_success_url(self):
        return reverse("deals:offer-detail", kwargs={"pk": self.object.pk})


class OfferDeleteView(ProtectedDeleteMixin, GetFormInstanceMixin, DeleteView):
    model = Offer
    form_class = OfferDeleteForm
    template_name = 'deals/offer_delete.html'
    success_url = reverse_lazy("deals:offer-list")
    success_message = "Offer {obj} was deleted successfully."
    protected_message = "Offer {obj} could not be deleted because it is in use."



class OfferDetailView(DetailView):
    model = Offer
    template_name = 'deals/offer_detail.html'
    context_object_name = "offer"
    queryset = Offer.objects.select_related("client", "pricing_year", "target_group")
