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
from trail_table import *

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

    def post(self, request, *args, **kwargs):
        if self.csv_download_button in self.request.POST:
            objects = self.get_queryset()
            if self.csv_limited_record:
                objects = objects[:self.csv_limited_record]

            csv_io = StringIO.StringIO()
            csv_wr = csv.writer(csv_io)

            def get_csv_val(o, f):
                v = o
                for subf in f.split('.'):
                    v = getattr(v, subf)

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
            return super(ExportCsvMixin, self).post(request, *args, **kwargs)

class ExportCsvMixin2(object):
    csv_limited_record2 = 10000
    csv_download_button2 = 'download_csv_click_count'
    def get_csv_filename(self):
        if self.csv_filename is None:
            raise Exception("ExportCsvMixin requires a definition of csv_filename")
        else:
            return self.csv_filename

    def post(self, request, *args, **kwargs):
        if self.csv_download_button2 in self.request.POST:
            objects = self.get_queryset()

            if self.csv_limited_record2:
                objects = objects[:self.csv_limited_record2]

            csv_io = StringIO.StringIO()
            csv_wr = csv.writer(csv_io)

            def get_csv_val(o, f):
                v = o
                for subf in f.split('.'):
                    v = getattr(v, subf)

                if isinstance(v, datetime.date):
                    v = localtime(v)

                return v

            c=Company()
            for obj in objects:
                csv_vals = map(lambda f: get_csv_val(obj, f), self.csv_fields)
                append = csv_vals_Append_Format(csv_vals)
                c.csv_append([append.acc_name,append.full_name,append.action,append.trail_hour,append.trail_date])
            for date in c.date:
                date_in_row=[]
                date_in_row.append(date)
                csv_wr.writerow(date_in_row)
                time=[]
                time.append("Time:")
                time_range=range(22,3,-1)
                for t in time_range:
                    time.append("%d:00"%t)
                csv_wr.writerow(time)

                for user in c.user:
                    user_trail=[]
                    user_trail.append(user)
                    for t in time_range:
                        user_trail.append(c.total_action(user,date,t))
                    csv_wr.writerow(user_trail)
                linespacing=[]
                csv_wr.writerow(linespacing)



            response = http.HttpResponse(mimetype='text/csv')
            filename = self.get_csv_filename()
            response['Content-Disposition'] = 'attachment; filename="{0}"'.format(filename)
            response.write(csv_io.getvalue())
            return response
        else:
            return super(ExportCsvMixin2, self).get(request, *args, **kwargs)

class CompanyAuditTrailsListView(ExportCsvMixin, ExportCsvMixin2, ListView):
    csv_filename = 'audit_trails.csv'
    csv_fields = ['user', 'user.fullname', 'action_name', 'created_time']
    template_name = 'companies/audit/trails/list.html'
    paginate_by = 30

    @method_decorator(permission_required(required_level=USER_ROLE_ADMIN_LEVEL))
    def dispatch(self, request, *args, **kwargs):
        return super(CompanyAuditTrailsListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        company_syscode = self.kwargs['system_code']
        trail_queryset = Trail.objects.filter(user__system__code=company_syscode)
        self.filter = AuditTrailFilter(self.request.POST, queryset=trail_queryset)
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
