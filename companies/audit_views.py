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
    model = Trail
    paginate_by = 30

    def get_queryset(self):
        self.filter = AuditTrailFilter(self.request.GET, queryset=Trail.objects.all())
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super(CompanyAuditTrailsListView, self).get_context_data(**kwargs)
        # f = AuditTrailFilter(self.request.GET, queryset=Trail.objects.all())
        context['filter'] = self.filter

        return context
