from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import CreateView, DeleteView, DetailView, FormView, ListView, TemplateView, UpdateView

from general.mixins import FilterQueryMixin, GetFormInstanceMixin, ProtectedDeleteMixin

from pricing.exceptions import PricingError
from pricing.forms import (
    ChannelDeleteForm,
    ChannelForm,
    IndexBandDeleteForm,
    IndexBandForm,
    MonthlyCoefficientsForm,
    PriceCalculatorForm,
    PricingYearDeleteForm,
    PricingYearForm,
    TargetGroupDeleteForm,
    TargetGroupForm,
    TargetGroupPriceDeleteForm,
    TargetGroupPriceEditForm,
    TargetGroupPriceForm,
)
from pricing.models import (
    Channel, IndexBand, Month, MonthlyCoefficient, PriceIndexType, PricingYear, TargetGroup, TargetGroupPrice
)
from pricing.services import calculate


def _int_or_none(value):
    """'12' -> 12, anything else -> None. Used for ?year= and ?group= filters."""
    return int(value) if value and value.isdigit() else None


# ------------------------------------------------- Pricing Home View
class PricingHomeView(TemplateView):
    template_name = 'pricing/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        counts = {
            'years': PricingYear.objects.count(),
            'channels': Channel.objects.count(),
            'groups': TargetGroup.objects.count(),
            'prices': TargetGroupPrice.objects.count(),
            'coefficients': MonthlyCoefficient.objects.count(),
            'bands': IndexBand.objects.count(),
        }

        has_year = counts['years'] > 0

        # At least one year with full range of 12 monthly coefficients.
        has_full_year = (
            PricingYear.objects
            .annotate(coefficients_count=Count('monthly_coefficients'))
            .filter(coefficients_count=12)
            .exists()
        )

        # At least one band for each price index type.
        has_prime_time_bands = IndexBand.objects.filter(
            index_type=PriceIndexType.PT
        ).exists()
        has_split_bands = IndexBand.objects.filter(
            index_type=PriceIndexType.CHANNEL_SPLIT
        ).exists()

        context['counts'] = counts
        context['has_year'] = has_year
        context['setup_complete'] = (
                has_year
                and counts['channels'] > 0
                and counts['groups'] > 0
                and counts['prices'] > 0
                and has_full_year
                and has_prime_time_bands
                and has_split_bands
        )

        return context


# ------------------------------------------------- PricingYear Views

class PricingYearListView(ListView):
    model = PricingYear
    paginate_by = 25
    template_name = 'years/years.html'
    context_object_name = 'years'

    def get_queryset(self):
        # distinct=True: several joins in one query would multiply the counts.
        # order_by is explicit: annotate() with Count() drops Meta.ordering.
        return super().get_queryset().annotate(
            prices_count=Count('group_prices', distinct=True),
            coefficients_count=Count('monthly_coefficients', distinct=True),
            bands_count=Count('index_bands', distinct=True),
        ).order_by('-year')


class PricingYearCreateView(SuccessMessageMixin, CreateView):
    model = PricingYear
    form_class = PricingYearForm
    success_url = reverse_lazy('pricing:year-list')
    template_name = 'years/year_create.html'
    success_message = 'Year %(year)s was created successfully.'


class PricingYearDetailView(DetailView):
    """The dashboard of one year: prices, 12 months, bands and warnings."""
    model = PricingYear
    template_name = 'years/year_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        year = self.object

        prices = year.group_prices.select_related('target_group')

        saved = dict(year.monthly_coefficients.values_list('month', 'coefficient'))
        months = [
            {'number': number, 'label': label, 'coefficient': saved.get(number)}
            for number, label in Month.choices
        ]
        missing_months = [m['label'] for m in months if m['coefficient'] is None]

        all_bands = list(year.index_bands.all())
        band_groups = []
        for value, label in PriceIndexType.choices:
            bands = [b for b in all_bands if b.index_type == value]
            band_groups.append({
                'value': value,
                'label': label,
                'bands': bands,
                'has_full_range': any(b.upper_limit == 100 for b in bands),
            })

        warnings = []
        if missing_months:
            warnings.append(
                f'Missing monthly coefficients: {", ".join(missing_months)}.'
            )
        for group in band_groups:
            if not group['has_full_range']:
                warnings.append(
                    f'{group["label"]}: there is no band with upper limit 100, '
                    'so high percentages will have no index.'
                )

        context.update({
            'prices': prices,
            'months': months,
            'missing_months': missing_months,
            'band_groups': band_groups,
            'warnings': warnings,
        })
        return context


class PricingYearDeleteView(ProtectedDeleteMixin, GetFormInstanceMixin, DeleteView):
    model = PricingYear
    form_class = PricingYearDeleteForm
    success_url = reverse_lazy('pricing:year-list')
    template_name = 'years/year_delete.html'
    success_message = 'Year {obj} was deleted successfully.'
    protected_message = 'Year has prices, coefficients or bands and cannot be deleted.'


# ----------------------------------------------------- Channel Views

class ChannelListView(ListView):
    model = Channel
    paginate_by = 25
    template_name = 'channels/channels.html'
    context_object_name = 'channels'

    def get_queryset(self):
        queryset = (
            super().get_queryset()
            .annotate(groups_count=Count('target_groups'))
            .order_by('name')
        )
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(name__icontains=query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '').strip()
        return context


class ChannelCreateView(SuccessMessageMixin, CreateView):
    model = Channel
    form_class = ChannelForm
    success_url = reverse_lazy('pricing:channel-list')
    template_name = 'channels/channel_create.html'
    success_message = 'Channel "%(name)s" was created successfully.'


class ChannelEditView(SuccessMessageMixin, UpdateView):
    model = Channel
    form_class = ChannelForm
    success_url = reverse_lazy('pricing:channel-list')
    template_name = 'channels/channel_edit.html'
    success_message = 'Channel "%(name)s" was edited successfully.'


class ChannelDeleteView(ProtectedDeleteMixin, GetFormInstanceMixin, DeleteView):
    """A channel is only linked through a many-to-many, so it is never protected."""
    model = Channel
    form_class = ChannelDeleteForm
    success_url = reverse_lazy('pricing:channel-list')
    template_name = 'channels/channel_delete.html'
    success_message = 'Channel "{obj}" was deleted successfully.'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['target_groups'] = self.object.target_groups.all()
        return context


# -------------------------------------------------- TargetGroup Views

class TargetGroupListView(ListView):
    model = TargetGroup
    paginate_by = 25
    template_name = 'groups/groups.html'
    context_object_name = 'groups'

    def get_queryset(self):
        queryset = (
            super().get_queryset()
            .prefetch_related('channels')
            .annotate(prices_count=Count('prices', distinct=True))
            .order_by('name')
        )
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(name__icontains=query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '').strip()
        return context


class TargetGroupDetailView(DetailView):
    model = TargetGroup
    template_name = 'groups/group_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['channels'] = self.object.channels.all()
        context['prices'] = self.object.prices.select_related('pricing_year')
        return context


class HasChannelsMixin:
    """The group form cannot be filled without channels: tell the template."""
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['has_channels'] = Channel.objects.exists()
        return context


class TargetGroupCreateView(HasChannelsMixin, SuccessMessageMixin, CreateView):
    model = TargetGroup
    form_class = TargetGroupForm
    success_url = reverse_lazy('pricing:group-list')
    template_name = 'groups/group_create.html'
    success_message = 'Target group "%(name)s" was created successfully.'


class TargetGroupEditView(HasChannelsMixin, SuccessMessageMixin, UpdateView):
    model = TargetGroup
    form_class = TargetGroupForm
    success_url = reverse_lazy('pricing:group-list')
    template_name = 'groups/group_edit.html'
    success_message = 'Target group "%(name)s" was edited successfully.'


class TargetGroupDeleteView(ProtectedDeleteMixin, GetFormInstanceMixin, DeleteView):
    model = TargetGroup
    form_class = TargetGroupDeleteForm
    success_url = reverse_lazy('pricing:group-list')
    template_name = 'groups/group_delete.html'
    success_message = 'Target group "{obj}" was deleted successfully.'
    protected_message = (
        'Target group "{obj}" has prices and cannot be deleted. '
        'Delete its prices first.'
    )


# ------------------------------------------------ TargetGroupPrice Views

class TargetGroupPriceListView(FilterQueryMixin, ListView):
    model = TargetGroupPrice
    paginate_by = 25
    template_name = 'prices/prices.html'
    context_object_name = 'prices'

    # Only these values are accepted from ?ordering=
    ORDERING_FIELDS = {
        'group': 'target_group__name',
        '-group': '-target_group__name',
        'price': 'base_price',
        '-price': '-base_price',
        'year': 'pricing_year__year',
        '-year': '-pricing_year__year',
    }

    def get_queryset(self):
        queryset = super().get_queryset().select_related('pricing_year', 'target_group')

        year_id = _int_or_none(self.request.GET.get('year'))
        if year_id:
            queryset = queryset.filter(pricing_year_id=year_id)

        group_id = _int_or_none(self.request.GET.get('group'))
        if group_id:
            queryset = queryset.filter(target_group_id=group_id)

        ordering = self.ORDERING_FIELDS.get(self.request.GET.get('ordering'))
        if ordering:
            # The second key keeps the order stable when values repeat.
            queryset = queryset.order_by(ordering, 'pk')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        ordering = self.request.GET.get('ordering', '')
        context.update({
            'years': PricingYear.objects.all(),
            'groups': TargetGroup.objects.all(),
            'selected_year': _int_or_none(self.request.GET.get('year')),
            'selected_group': _int_or_none(self.request.GET.get('group')),
            'ordering': ordering if ordering in self.ORDERING_FIELDS else '',
        })
        return context


class TargetGroupPriceCreateView(SuccessMessageMixin, CreateView):
    model = TargetGroupPrice
    form_class = TargetGroupPriceForm
    success_url = reverse_lazy('pricing:price-list')
    template_name = 'prices/price_create.html'
    success_message = 'Price for %(target_group)s / %(pricing_year)s was created successfully.'

    def get_initial(self):
        initial = super().get_initial()
        year_id = _int_or_none(self.request.GET.get('year'))
        group_id = _int_or_none(self.request.GET.get('group'))
        if year_id:
            initial['pricing_year'] = year_id
        if group_id:
            initial['target_group'] = group_id
        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['has_years'] = PricingYear.objects.exists()
        context['has_groups'] = TargetGroup.objects.exists()
        return context


class TargetGroupPriceEditView(SuccessMessageMixin, UpdateView):
    model = TargetGroupPrice
    form_class = TargetGroupPriceEditForm
    success_url = reverse_lazy('pricing:price-list')
    template_name = 'prices/price_edit.html'

    def get_queryset(self):
        return super().get_queryset().select_related('pricing_year', 'target_group')

    def get_success_message(self, cleaned_data):
        return f'Price for {self.object.target_group} / {self.object.pricing_year} was updated.'


class TargetGroupPriceDeleteView(ProtectedDeleteMixin, GetFormInstanceMixin, DeleteView):
    model = TargetGroupPrice
    form_class = TargetGroupPriceDeleteForm
    success_url = reverse_lazy('pricing:price-list')
    template_name = 'prices/price_delete.html'
    success_message = 'Price {obj} was deleted successfully.'

    def get_queryset(self):
        return super().get_queryset().select_related('pricing_year', 'target_group')


# ---------------------------------------------- Monthly coefficients View

class YearCoefficientsView(FormView):
    form_class = MonthlyCoefficientsForm
    template_name = 'years/year_coefficients.html'

    def dispatch(self, request, *args, **kwargs):
        self.pricing_year = get_object_or_404(PricingYear, pk=kwargs['pk'])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['pricing_year'] = self.pricing_year
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pricing_year'] = self.pricing_year
        return context

    def form_valid(self, form):
        form.save()
        messages.success(
            self.request,
            f'Monthly coefficients for {self.pricing_year} were saved.',
        )
        return redirect('pricing:year-detail', pk=self.pricing_year.pk)


# ------------------------------------------------------- IndexBand Views

class IndexBandListView(FilterQueryMixin, ListView):
    model = IndexBand
    paginate_by = 25
    template_name = 'bands/bands.html'
    context_object_name = 'bands'

    def get_queryset(self):
        # The model ordering is: year (newest first), type, upper limit.
        queryset = super().get_queryset().select_related('pricing_year')

        year_id = _int_or_none(self.request.GET.get('year'))
        if year_id:
            queryset = queryset.filter(pricing_year_id=year_id)

        index_type = self.request.GET.get('type')
        if index_type in PriceIndexType.values:
            queryset = queryset.filter(index_type=index_type)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        index_type = self.request.GET.get('type')
        context.update({
            'years': PricingYear.objects.all(),
            'index_types': PriceIndexType.choices,
            'selected_year': _int_or_none(self.request.GET.get('year')),
            'selected_type': index_type if index_type in PriceIndexType.values else '',
        })
        return context


class IndexBandCreateView(SuccessMessageMixin, CreateView):
    model = IndexBand
    form_class = IndexBandForm
    template_name = 'bands/band_create.html'
    success_message = 'Band "up to %(upper_limit)s%%" was created successfully.'

    def get_initial(self):
        """?year= and ?type= prefill the form, handy for entering a series of bands."""
        initial = super().get_initial()
        year_id = _int_or_none(self.request.GET.get('year'))
        index_type = self.request.GET.get('type')
        if year_id:
            initial['pricing_year'] = year_id
        if index_type in PriceIndexType.values:
            initial['index_type'] = index_type
        return initial

    def get_success_url(self):
        # Back to the list of the same year and type that was just edited.
        return (
            f'{reverse("pricing:band-list")}'
            f'?year={self.object.pricing_year_id}&type={self.object.index_type}'
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['has_years'] = PricingYear.objects.exists()
        return context


class IndexBandDeleteView(ProtectedDeleteMixin, GetFormInstanceMixin, DeleteView):
    model = IndexBand
    form_class = IndexBandDeleteForm
    success_url = reverse_lazy('pricing:band-list')
    template_name = 'bands/band_delete.html'
    success_message = 'Band was deleted successfully.'

    def get_queryset(self):
        return super().get_queryset().select_related('pricing_year')


# ----------------------------------------------------- Calculator View

class PriceCalculatorView(FormView):
    """
    GET only. The form is bound to the query string when it holds form data.
    ?year=<id> alone only preselects the year (used by the year dashboard).
    """
    form_class = PriceCalculatorForm
    template_name = 'calculator.html'
    http_method_names = ['get', 'head', 'options']

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if any(name in self.request.GET for name in PriceCalculatorForm.base_fields):
            kwargs['data'] = self.request.GET

        year_id = _int_or_none(self.request.GET.get('year'))
        if year_id:
            kwargs['initial'] = {**kwargs.get('initial', {}), 'pricing_year': year_id}
        return kwargs

    def get(self, request, *args, **kwargs):
        form = self.get_form()
        result = None

        if form.is_bound and form.is_valid():
            try:
                result = calculate(
                    form.cleaned_data['pricing_year'],
                    form.cleaned_data['target_group'],
                    form.cleaned_data['pt_percent'],
                    form.cleaned_data['main_channel_percent'],
                )
            except PricingError as error:
                form.add_error(None, str(error))

        return self.render_to_response(self.get_context_data(form=form, result=result))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        has_years = PricingYear.objects.exists()
        has_groups = TargetGroup.objects.exists()
        has_prices = TargetGroupPrice.objects.exists()
        context.update({
            'has_years': has_years,
            'has_groups': has_groups,
            'has_prices': has_prices,
            'ready': has_years and has_groups and has_prices,
        })
        return context