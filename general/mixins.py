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