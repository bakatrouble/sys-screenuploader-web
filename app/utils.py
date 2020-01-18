from django.forms import ModelForm
from django.views.generic import TemplateView

from app.forms import DestinationForm
from app.models import Destination


def get_config_form(mdl):
    class ConfigForm(ModelForm):
        prefix = 'config'

        class Meta:
            model = mdl
            exclude = mdl.EXCLUDE_FIELDS if hasattr(mdl, 'EXCLUDE_FIELDS') else ()
            widgets = mdl.CUSTOM_WIDGETS if hasattr(mdl, 'CUSTOM_WIDGETS') else {}
    return ConfigForm


class BaseDestinationView(TemplateView):
    template_name = 'cabinet/destination_form.html'
    context_object_name = 'destination'

    def get_queryset(self):
        return Destination.objects.filter(owner=self.request.user)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        destination_form, config_form = self.get_forms()
        if destination_form.is_valid() and config_form.is_valid():
            return self.form_valid(destination_form, config_form)
        else:
            context = self.get_context_data(forms=(destination_form, config_form))
            return self.render_to_response(context)

    def get_forms(self):
        destination = self.get_object()
        data = self.request.POST if self.request.method == 'POST' else None
        files = self.request.FILES if self.request.method == 'POST' else None
        return DestinationForm(data=data, files=files, instance=destination), \
               get_config_form(self.get_content_type().model_class())(data=data, files=files,
                                                                      instance=destination.config if destination else None)

    def get_context_data(self, forms=None, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['destination_form'], ctx['config_form'] = self.get_forms() if forms is None else forms
        ctx['module'] = self.get_content_type().model_class()
        return ctx
