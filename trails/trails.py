from django.views.generic.list import ListView
from django.utils.decorators import method_decorator
from system.models import System
from user.models import USER_ROLE_ADMIN_LEVEL
from utils.auth import permission_required_trails
from audit.models import Trail


class CompanyAuditTrailsListView(ListView):
    template_name = 'trails/list.html'

    @method_decorator(permission_required_trails(required_level=USER_ROLE_ADMIN_LEVEL))
    def dispatch(self, request, *args, **kwargs):
        return super(CompanyAuditTrailsListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        trail_queryset = Trail.objects.all()
        return trail_queryset

    def get_context_data(self, **kwargs):
        context = super(CompanyAuditTrailsListView, self).get_context_data(**kwargs)
        context['systems'] = System.objects.all()
        return context
