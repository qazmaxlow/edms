from django.contrib.auth import get_user_model
from django.shortcuts import render
from django.views.generic.list import ListView

import django_filters

from audit.models import Trail


class AuditTrailFilter(django_filters.FilterSet):
    class Meta:
        model = Trail
        fields = ['user',]

    def __init__(self, company_syscode, *args, **kwargs):
        super(AuditTrailFilter, self).__init__(*args, **kwargs)
        User = get_user_model()
        user_queryset = User.objects.filter(system__code=company_syscode)
        self.filters['user'].extra.update(
            {'empty_label': 'All user',
             'queryset': user_queryset,
         })


class CompanyAuditTrailsListView(ListView):
    template_name = 'companies/audit/trails/list.html'
    paginate_by = 30

    def get_queryset(self):
        company_syscode = self.kwargs['system_code']
        trail_queryset = Trail.objects.filter(user__system__code=company_syscode)
        self.filter = AuditTrailFilter(company_syscode, self.request.GET, queryset=trail_queryset)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super(CompanyAuditTrailsListView, self).get_context_data(**kwargs)
        context['filter'] = self.filter

        return context
