from django.shortcuts import render
from django.views.generic import TemplateView
from django.utils.decorators import method_decorator

from system.models import System
from utils.auth import permission_required
from audit.decorators.trail import log_audit_trail
from constants.audits import ACTION_VIEW_GOAL_SETTING

class SystemGoalSettingsView(TemplateView):
    template_name="systems/goals/settings.html"

    @method_decorator(permission_required())
    @method_decorator(log_audit_trail(action_type=ACTION_VIEW_GOAL_SETTING))
    def dispatch(self, request, *args, **kwargs):
        return super(SystemGoalSettingsView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(SystemGoalSettingsView, self).get_context_data(**kwargs)
        syscode = self.kwargs['system_code']

        systems_info = System.get_systems_info(syscode, self.request.user.system.code)
        context = systems_info

        context['current_system'] = systems_info['systems'][0]
        context['current_user'] = self.request.user

        return context
