from django.shortcuts import render
from utils.auth import permission_required
from system.models import System

@permission_required()
def dashboard_view(request, system_code):

    systems_info = System.get_systems_info(system_code, request.user.system.code)
    m = systems_info

    return render(request, 'companies/dashboard/dashboard.html', m)