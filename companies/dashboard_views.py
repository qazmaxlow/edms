import datetime
import json
import pytz

from dateutil.relativedelta import relativedelta
from django.shortcuts import render
from django.utils import dateparse
from django.utils import timezone
from system.models import System
from utils.auth import permission_required
from operator import itemgetter

from egauge.manager import SourceManager

@permission_required()
def dashboard_view(request, system_code):

    systems_info = System.get_systems_info(system_code, request.user.system.code)
    current_system = systems_info['systems'][0]

    m = systems_info
    m['current_system'] = current_system

    return render(request, 'companies/dashboard/dashboard.html', m)
