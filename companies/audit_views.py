from django.shortcuts import render
from django.views.generic.list import ListView

from audits.models import Trail


class CompanyAuditTrailListView(ListView):
    template_name = 'companies/audit/trails/list.html'
    model = Trail
