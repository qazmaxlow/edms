from django.shortcuts import render
from django.views.generic.list import ListView

import django_filters

from audit.models import Trail


class AuditTrailFilter(django_filters.FilterSet):
    class Meta:
        model = Trail
        fields = ['user',]


class CompanyAuditTrailsListView(ListView):
    template_name = 'companies/audit/trails/list.html'
    paginate_by = 30

    def get_queryset(self):
        company_syscode = self.kwargs['system_code']
        trail_queryset = Trail.objects.filter(user__system__code=company_syscode)
        self.filter = AuditTrailFilter(self.request.GET, queryset=trail_queryset)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super(CompanyAuditTrailsListView, self).get_context_data(**kwargs)
        context['filter'] = self.filter

        return context
