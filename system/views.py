from django.shortcuts import render
from django.views.generic import TemplateView

from system.models import System


class SystemGoalSettingsView(TemplateView):
    template_name="systems/goals/settings.html"

    def get_context_data(self, **kwargs):
        context = super(SystemGoalSettingsView, self).get_context_data(**kwargs)
        syscode = self.kwargs['system_code']

        systems_info = System.get_systems_info(syscode, self.request.user.system.code)
        context = systems_info

        context['current_system'] = systems_info['systems'][0]
        context['current_user'] = self.request.user

        return context
