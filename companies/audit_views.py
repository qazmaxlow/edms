from django.shortcuts import render
from django.views.generic.list import ListView

from audit.models import Trail


class CompanyAuditTrailsListView(ListView):
    template_name = 'companies/audit/trails/list.html'
    model = Trail
    paginate_by = 30
