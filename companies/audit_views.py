from django.contrib.auth import get_user_model
from django import forms
from django.db import models
from django.shortcuts import render
from django.views.generic.list import ListView
from django.utils.decorators import method_decorator

import django_filters

from audit.models import Trail
from system.models import System
from user.models import USER_ROLE_ADMIN_LEVEL
from utils.auth import permission_required


class DateTimeField(forms.DateTimeField):
    def widget_attrs(self, widget):
        attrs = super(DateTimeField, self).widget_attrs(widget)
        attrs.update({
            'kendo-date-picker': 'kendo-date-picker',
            'k-format': "'yyyy-MM-dd'",
        })
        return attrs


class DateTimeFilter(django_filters.DateTimeFilter):
    field_class = DateTimeField


class AuditTrailFilter(django_filters.FilterSet):
    filter_overrides = {
        models.DateTimeField: {
            'filter_class': DateTimeFilter,
        }
    }

    class Meta:
        model = Trail
        fields = {'user': ['exact'], 'created_time': ['gte', 'lte']}

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

    @method_decorator(permission_required(required_level=USER_ROLE_ADMIN_LEVEL))
    def dispatch(self, request, *args, **kwargs):
        return super(CompanyAuditTrailsListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        company_syscode = self.kwargs['system_code']
        trail_queryset = Trail.objects.filter(user__system__code=company_syscode)
        self.filter = AuditTrailFilter(company_syscode, self.request.GET, queryset=trail_queryset)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super(CompanyAuditTrailsListView, self).get_context_data(**kwargs)
        context['filter'] = self.filter

        company_syscode = self.kwargs['system_code']
        company_system = System.objects.get(code=company_syscode)
        context['company_system'] = company_system

        return context
