from django.views.generic import TemplateView


class DealHomeView(TemplateView):
    template_name = 'home.html'
