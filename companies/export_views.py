from django.views.generic import TemplateView
from django.utils.decorators import method_decorator

from system.models import System

from utils.auth import permission_required


class ExportView(TemplateView):
    template_name="companies/export/index.html"

    @method_decorator(permission_required())
    def dispatch(self, request, *args, **kwargs):
        return super(ExportView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ExportView, self).get_context_data(**kwargs)
        # context['system_code'] =
        syscode = self.kwargs['system_code']

        systems_info = System.get_systems_info(syscode, self.request.user.system.code)
        context = systems_info

        context['current_system'] = systems_info['systems'][0]
        return context
