from urllib.parse import urlencode

from django.contrib import messages
from django.db.models import ProtectedError
from django.http import HttpResponseRedirect


class DisableFieldsMixin:
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.disabled = True

class GetFormInstanceMixin:
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['instance'] = self.object
        return kwargs


class ProtectedDeleteMixin:
    """
    For DeleteView. Deletes the object, or shows an error message when
    related rows (on_delete=PROTECT) forbid it. Both messages may use {obj}.
    """
    success_message = '{obj} was deleted successfully.'
    protected_message = '{obj} cannot be deleted because it is in use.'

    def form_valid(self, form):
        label = str(self.object)
        try:
            self.object.delete()
        except ProtectedError:
            messages.error(self.request, self.protected_message.format(obj=label))
        else:
            messages.success(self.request, self.success_message.format(obj=label))
        return HttpResponseRedirect(self.get_success_url())


class FilterQueryMixin:
    """
    For ListView. Adds `filter_query` (the current GET parameters without `page`)
    to the context, so pagination links keep the active filters and ordering.
    """
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        params = {
            key: value for key, value in self.request.GET.items()
            if key != 'page' and value
        }
        context['filter_query'] = urlencode(params)
        return context
