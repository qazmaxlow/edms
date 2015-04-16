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

    today = timezone.now().astimezone(current_system_tz).replace(hour=0, minute=0, second=0, microsecond=0)

    last_week_start_dt = today - relativedelta(days=7+today.isoweekday())
    last_week_end_dt = today - relativedelta(days=1+today.isoweekday())

    two_weeks_ago_start_dt = last_week_start_dt - relativedelta(days=7)
    two_weeks_ago_end_dt = last_week_end_dt - relativedelta(days=7)

    m = systems_info
    last_week_overnight_stats = System.reports.overnight_cost_by_day(current_system, last_week_start_dt, last_week_end_dt)
    two_weeks_ago_overnight_stats = System.reports.overnight_cost_by_day(current_system, two_weeks_ago_start_dt, two_weeks_ago_end_dt)

    if last_week_overnight_stats['number_of_days'] > 0:
        m['last_week_overnight_average'] = last_week_overnight_stats['total']/float(last_week_overnight_stats['number_of_days'])
    else:
        m['last_week_overnight_average'] = 0

    if two_weeks_ago_overnight_stats['number_of_days'] > 0:
        m['two_weeks_ago_overnight_average'] = two_weeks_ago_overnight_stats['total']/float(two_weeks_ago_overnight_stats['number_of_days'])
    else:
        m['two_weeks_ago_overnight_average'] = 0

    if m['two_weeks_ago_overnight_average'] > 0:
        m['overnight_percentage_change'] = (m['last_week_overnight_average']-m['two_weeks_ago_overnight_average'])*100/float(m['two_weeks_ago_overnight_average'])
    else:
        m['overnight_percentage_change'] = 0

    last_week_weekday_stats = System.reports.weekday_cost_by_day(current_system, last_week_start_dt, last_week_end_dt)
    two_weeks_ago_weekday_stats = System.reports.weekday_cost_by_day(current_system, two_weeks_ago_start_dt, two_weeks_ago_end_dt)

    if last_week_weekday_stats['number_of_days'] > 0:
        m['last_week_weekday_average'] = last_week_weekday_stats['total']/float(last_week_weekday_stats['number_of_days'])
    else:
        m['last_week_weekday_average'] = 0

    if two_weeks_ago_weekday_stats['number_of_days'] > 0:
        m['two_weeks_ago_weekday_average'] = two_weeks_ago_weekday_stats['total']/float(two_weeks_ago_weekday_stats['number_of_days'])
    else:
        m['two_weeks_ago_weekday_average'] = 0

    if m['two_weeks_ago_weekday_average'] > 0:
        m['weekday_percentage_change'] = (m['last_week_weekday_average']-m['two_weeks_ago_weekday_average'])*100/float(m['two_weeks_ago_weekday_average'])
    else:
        m['weekday_percentage_change'] = 0

    dates_with_overnight_data = [s['date'] for s in last_week_overnight_stats['data']]
    dates_with_weekday_data = [s['date'] for s in last_week_weekday_stats['data']]

    for single_date in daterange(last_week_start_dt, last_week_end_dt + relativedelta(days=1)):
        if single_date.strftime("%Y-%m-%d") not in dates_with_overnight_data:
            last_week_overnight_stats['data'].append({'date':single_date.strftime("%Y-%m-%d"), 'weekday':single_date.strftime("%a"), 'value':0})
        if single_date.strftime("%Y-%m-%d") not in dates_with_weekday_data and single_date.weekday() <= 4:
            last_week_weekday_stats['data'].append({'date':single_date.strftime("%Y-%m-%d"), 'weekday':single_date.strftime("%a"), 'value':0})

    m["last_week_overnight_stats"] = json.dumps(sorted(last_week_overnight_stats['data'], key=itemgetter('date')))
    m["last_week_weekday_stats"] = json.dumps(sorted(last_week_weekday_stats['data'], key=itemgetter('date')))

    return render(request, 'companies/dashboard/dashboard.html', m)
