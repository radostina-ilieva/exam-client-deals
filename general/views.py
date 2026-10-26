from django.views.generic import TemplateView

from clients.models import Client, Sector
from deals.models import Offer


class DealHomeView(TemplateView):
    template_name = 'home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['clients_count'] = Client.objects.count()
        context['sectors_count'] = Sector.objects.count()
        context['offers_count'] = Offer.objects.count()

        context['recent_offers'] = (
            Offer.objects
            .select_related('client')
            .order_by('-created_at', '-pk')[:5]
        )

        return context
