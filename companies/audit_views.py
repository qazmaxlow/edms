import csv, datetime
import StringIO

from django.contrib.auth import get_user_model
from django.db import models
from django import http
from django.shortcuts import render
from django.views.generic.list import ListView
from django.utils.decorators import method_decorator
from django.utils.timezone import localtime

import django_filters

from audit.models import Trail
from system.models import System
from user.models import USER_ROLE_ADMIN_LEVEL
from utils.auth import permission_required


class AuditTrailFilter(django_filters.FilterSet):

    class Meta:
        model = Trail
        fields = {'user': ['exact'], 'created_time': ['gte', 'lte']}

class ExportCsvMixin(object):
    csv_limited_record = 10000
    csv_download_button = 'download_csv'

    def get_csv_filename(self):
        if self.csv_filename is None:
            raise Exception("ExportCsvMixin requires a definition of csv_filename")
        else:
            return self.csv_filename

    def get(self, request, *args, **kwargs):
        if self.csv_download_button in self.request.GET:
            objects = self.get_queryset()
            if self.csv_limited_record:
                objects = objects[:self.csv_limited_record]

            csv_io = StringIO.StringIO()
            csv_wr = csv.writer(csv_io)

            def get_csv_val(o, f):
                v = getattr(o, f)
                if isinstance(v, datetime.date):
                    v = localtime(v)

                return v

            for obj in objects:
                csv_vals = map(lambda f: get_csv_val(obj, f), self.csv_fields)
                csv_wr.writerow(csv_vals)

            response = http.HttpResponse(mimetype='text/csv')
            filename = self.get_csv_filename()
            response['Content-Disposition'] = 'attachment; filename="{0}"'.format(filename)
            response.write(csv_io.getvalue())
            return response
        else:
            return super(ExportCsvMixin, self).get(request, *args, **kwargs)


class CompanyAuditTrailsListView(ExportCsvMixin, ListView):
    csv_filename = 'audit_trails.csv'
    csv_fields = ['user', 'user_fullname', 'action_name', 'created_time']
    template_name = 'companies/audit/trails/list.html'
    paginate_by = 30

    @method_decorator(permission_required(required_level=USER_ROLE_ADMIN_LEVEL))
    def dispatch(self, request, *args, **kwargs):
        return super(CompanyAuditTrailsListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        company_syscode = self.kwargs['system_code']
        trail_queryset = Trail.objects.filter(user__system__code=company_syscode)
        self.filter = AuditTrailFilter(self.request.GET, queryset=trail_queryset)
        return self.filter.qs

    def get_context_data(self, **kwargs):
        context = super(CompanyAuditTrailsListView, self).get_context_data(**kwargs)
        context['filter'] = self.filter
        company_syscode = self.kwargs['system_code']
        User = get_user_model()
        context['users'] = User.objects.filter(system__code=company_syscode)

        company_syscode = self.kwargs['system_code']
        company_system = System.objects.get(code=company_syscode)
        context['company_system'] = company_system

        return context
