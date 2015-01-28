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
from companies.trail_table import *
from audit.models import Trail
from system.models import System
from user.models import *
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
                if obj.user.system!=None:
                    csv_vals.insert(0, obj.user.system.name)
                else:
                    csv_vals.insert(0,"")
                csv_wr.writerow(csv_vals)
                
                

            response = http.HttpResponse(mimetype='text/csv')
            filename = self.get_csv_filename()
            response['Content-Disposition'] = 'attachment; filename="{0}"'.format(filename)
            response.write(csv_io.getvalue())
            return response
        else:
            return super(ExportCsvMixin, self).post(request, *args, **kwargs)

class CompanyAuditTrailsListView(ExportCsvMixin, ListView):
    csv_filename = 'audit_trails.csv'
    csv_fields = ['user', 'user.fullname', 'action_name', 'created_time']
    template_name = 'companies/list.html'
    paginate_by = 30
    
    def dispatch(self, request, *args, **kwargs):
        return super(CompanyAuditTrailsListView, self).dispatch(request, *args, **kwargs)

    def get_queryset(self):
        company_syscode = '124'
        trail_queryset = Trail.objects.all()
        self.filter = AuditTrailFilter(self.request.POST, queryset=trail_queryset)
        return self.filter.qs


