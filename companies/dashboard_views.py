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

    def daterange(start_date, end_date):
        for n in range(int ((end_date - start_date).days)):
            yield start_date + datetime.timedelta(n)

    systems_info = System.get_systems_info(system_code, request.user.system.code)
    current_system = systems_info['systems'][0]
    sources = SourceManager.get_sources(current_system)
    current_system_tz = pytz.timezone(current_system.timezone)

    today = timezone.now().astimezone(current_system_tz)

    last_week_start_dt = today.replace(hour=0, minute=0, microsecond=0) - relativedelta(days=7+today.isoweekday())
    last_week_end_dt = today.replace(hour=0, minute=0, microsecond=0) - relativedelta(days=1+today.isoweekday())

    two_weeks_ago_start_dt = last_week_start_dt - relativedelta(days=7)
    two_weeks_ago_end_dt = last_week_start_dt - relativedelta(days=7)

    m = systems_info
    last_week_overnight_stats = System.reports.overnight_cost_by_day(current_system, last_week_start_dt, last_week_end_dt)
    two_weeks_ago_overnight_stats = System.reports.overnight_cost_by_day(current_system, two_weeks_ago_start_dt, two_weeks_ago_end_dt)

    last_week_overnight_total = 0
    last_week_overnight_number_of_days = 0
    two_weeks_ago_overnight_total = 0
    two_weeks_ago_overnight_number_of_days = 0

    for stat in last_week_overnight_stats:
        last_week_overnight_total += stat['value']
        last_week_overnight_number_of_days += 1

    for stat in two_weeks_ago_overnight_stats:
        two_weeks_ago_overnight_total += stat['value']
        two_weeks_ago_overnight_number_of_days += 1

    m['last_week_overnight_average'] = last_week_overnight_total/last_week_overnight_number_of_days
    m['two_weeks_ago_overnight_average'] = two_weeks_ago_overnight_total/two_weeks_ago_overnight_number_of_days
    m['overnight_percentage_change'] = float(m['last_week_overnight_average']-m['two_weeks_ago_overnight_average'])/m['two_weeks_ago_overnight_average']

    dates_with_overnight_data = [s['date'] for s in last_week_overnight_stats]

    for single_date in daterange(last_week_start_dt, last_week_end_dt + relativedelta(days=1)):
        if single_date.strftime("%Y-%m-%d") not in dates_with_overnight_data:
            last_week_overnight_stats.append({'date':single_date.strftime("%Y-%m-%d"), 'weekday':single_date.strftime("%a"), 'value':0})


    m["last_week_overnight_stats"] = json.dumps(sorted(last_week_overnight_stats, key=itemgetter('date')))

    return render(request, 'companies/dashboard/dashboard.html', m)