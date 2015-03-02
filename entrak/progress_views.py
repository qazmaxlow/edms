import datetime
import pytz
import calendar
import json
from django.shortcuts import render
from django.db.models import Q
from django.utils.translation import ugettext_lazy as _
from django.core.context_processors import csrf
from django.views.decorators.csrf import ensure_csrf_cookie
from settings import STATIC_URL
from system.models import System
from unit.models import UnitRate, CO2_CATEGORY_CODE, MONEY_CATEGORY_CODE
from baseline.models import BaselineUsage
from utils.auth import permission_required
from utils.utils import Utils
from egauge.manager import SourceManager
from egauge.models import SourceReadingMonth
from utils import calculation
from utils.utils import Utils
from audit.decorators.trail import log_audit_trail
from constants import audits as constants_audits

REDUCTION_LEVELS = [0, 2, 4, 6, 8, 10, 12, 14]
HK_TAXI_TRIP = {'multiplicand': 0.0033, 'from': _('Hong Kong Airport'), 'to': _('Times Square')}
TAXI_TRIP_INFO = {
    'hk': HK_TAXI_TRIP,
    'sg': {'multiplicand': 0.04, 'from': _('Singapore Airport'), 'to': _('Marina Bay Sands')},
}

def get_last_12_month_co2_consumption(unit_code, unit_rates, baselines, system, readings, current_dt):
    source_tz = pytz.timezone(system.timezone)
    end_dt = current_dt.astimezone(source_tz)
    end_dt = Utils.add_month(end_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0), -1)
    system_first_record = system.first_record.astimezone(source_tz)

    co2_consumption = 0
    for month_diff in xrange(12):
        target_dt = Utils.add_month(end_dt, -month_diff)
        timestamp = calendar.timegm(target_dt.utctimetuple())
        if timestamp in readings:
            energy_usage = readings[timestamp]
        else:
            # use baseline val for the missing month
            if target_dt.month in baselines:
                energy_usage = baselines[target_dt.month]['usage']
            else:
                energy_usage = 0

        # need to add missing day from baseline
        if (target_dt.year == system_first_record.year and target_dt.month == system_first_record.month) \
            and system_first_record.day != 1 \
            and target_dt.month in baselines:
            missing_day_num = system_first_record.day - 1
            days_of_month = calendar.monthrange(system_first_record.year, system_first_record.month)[1]
            energy_usage += (baselines[target_dt.month]['usage']/days_of_month)*missing_day_num

        co2_consumption += calculation.transform_reading(unit_code, timestamp,
            energy_usage, unit_rates)

    return co2_consumption

def calulcate_accumulated_saving(co2_unit_code, money_unit_code, co2_unit_rates, money_unit_rates,
    baselines, source_tz, first_record, readings, current_dt):
    start_dt = first_record.astimezone(source_tz)
    if start_dt.day != 1:
        # skip the incomplete month
        start_dt = start_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        start_dt = Utils.add_month(start_dt, 1)
    else:
        start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    end_dt = Utils.add_month(current_dt.astimezone(source_tz).replace(day=1, hour=0, minute=0, second=0, microsecond=0), -1)

    total_co2_saving = 0
    total_money_saving = 0

    target_dt = start_dt
    while target_dt <= end_dt:
        timestamp = calendar.timegm(target_dt.utctimetuple())
        energy_usage = readings.get(timestamp, 0)
        if target_dt.month in baselines:
            baseline_usage = baselines[target_dt.month]['usage']
        else:
            baseline_usage = 0
        usage_diff = baseline_usage - energy_usage

        total_co2_saving += calculation.transform_reading(co2_unit_code, timestamp,
            usage_diff, co2_unit_rates)
        total_money_saving += calculation.transform_reading(money_unit_code, timestamp,
            usage_diff, money_unit_rates)

        target_dt = Utils.add_month(target_dt, 1)

    return {'co2': total_co2_saving, 'money': total_money_saving}

def __calculate_progress_data(systems):
    current_system = systems[0]
    sources = SourceManager.get_sources(current_system)
    need_calculate_systems = System.assign_source_under_system(systems, sources)

    grouped_baselines = BaselineUsage.get_baselines_for_systems([system.id for system in need_calculate_systems.keys()])

    current_dt = pytz.utc.localize(datetime.datetime.utcnow())

    monthly_source_readings = SourceReadingMonth.objects(source_id__in=[str(source.id) for source in sources])
    grouped_monthly_readings = SourceManager.group_readings_with_source_id(monthly_source_readings)

    unit_rates = UnitRate.objects.filter(Q(category_code=CO2_CATEGORY_CODE) | Q(category_code=MONEY_CATEGORY_CODE))
    co2_unit_rates = [unit_rate for unit_rate in unit_rates if unit_rate.category_code == CO2_CATEGORY_CODE]
    money_unit_rates = [unit_rate for unit_rate in unit_rates if unit_rate.category_code == MONEY_CATEGORY_CODE]

    total_baseline_co2_consumption = 0
    last_12_months_co2_consumption = 0
    total_co2_saving = 0
    total_money_saving = 0
    for system, attached_sources in need_calculate_systems.items():
        baselines = grouped_baselines[system.id]
        baseline_monthly_usages = BaselineUsage.transform_to_monthly_usages(baselines, pytz.timezone(system.timezone))

        unit_info = json.loads(system.unit_info)
        co2_unit_code = unit_info[CO2_CATEGORY_CODE]
        money_unit_code = unit_info[MONEY_CATEGORY_CODE]

        baseline_co2_consumption = 0
        for month, month_info in baseline_monthly_usages.items():
            timestamp = calendar.timegm(month_info['dt'].utctimetuple())
            baseline_co2_consumption += calculation.transform_reading(co2_unit_code, timestamp,
                month_info['usage'], co2_unit_rates)
        total_baseline_co2_consumption += baseline_co2_consumption

        combined_readings = {}
        for source in attached_sources:
            target_readings = grouped_monthly_readings.get(str(source.id), {})
            for timestamp, reading in target_readings.items():
                combined_readings[timestamp] = combined_readings.get(timestamp, 0) + reading

        co2_consumption = get_last_12_month_co2_consumption(co2_unit_code, co2_unit_rates, baseline_monthly_usages,
            system, combined_readings, current_dt)
        last_12_months_co2_consumption += co2_consumption

        savings = calulcate_accumulated_saving(co2_unit_code, money_unit_code,
            co2_unit_rates, money_unit_rates, baseline_monthly_usages, pytz.timezone(system.timezone),
            system.first_record, combined_readings, current_dt)
        total_co2_saving += savings['co2']
        total_money_saving += savings['money']

    first_day_record = pytz.utc.localize(datetime.datetime(3000, 1, 1))
    first_day_tz = None
    for system in need_calculate_systems.keys():
        if system.first_record < first_day_record:
            first_day_record = system.first_record
            first_day_tz = system.timezone
    first_day_record = first_day_record.astimezone(pytz.timezone(first_day_tz))

    result = {}
    result['static_url'] = STATIC_URL
    result['last_12_months_co2_consumption_accurate'] = last_12_months_co2_consumption
    if total_baseline_co2_consumption != 0:
        result['percengate_change'] = (total_baseline_co2_consumption-last_12_months_co2_consumption)/total_baseline_co2_consumption*100.0
    else:
        result['percengate_change'] = 0
    result['total_co2_saving_in_kg'] = total_co2_saving
    result['total_co2_saving'] = int(total_co2_saving/1000)
    result['total_money_saving'] = total_money_saving
    result['first_day_record'] = first_day_record

    archived_level = REDUCTION_LEVELS[0]
    target_level = REDUCTION_LEVELS[1]
    for level_idx, level in enumerate(REDUCTION_LEVELS):
        if result['percengate_change'] >= level:
            archived_level = level
            target_level = REDUCTION_LEVELS[min(level_idx+1, len(REDUCTION_LEVELS)-1)]
    result['archived_level'] = archived_level
    result['target_level'] = target_level

    return result


@log_audit_trail(action_type=constants_audits.ACTION_VIEW_PROGRESS)
@permission_required()
@ensure_csrf_cookie
def progress_view(request, system_code=None):
    systems_info = System.get_systems_info(system_code, request.user.system.code)
    result = __calculate_progress_data(systems_info['systems'])
    current_system = systems_info['systems'][0]
    total_co2_saving = result['total_co2_saving_in_kg']
    total_money_saving = result['total_money_saving']

    m = systems_info
    m.update(result)
    m['elephant_num'] = int(round(total_co2_saving*0.00033))
    taxi_trip_info = TAXI_TRIP_INFO.get(current_system.city, HK_TAXI_TRIP)
    m['taxi_trip'] = {
        'count': int(round(total_money_saving*taxi_trip_info['multiplicand'])),
        'from': taxi_trip_info['from'],
        'to': taxi_trip_info['to']
    }
    m['saving_css_class'] = 'positive-saving' if m['percengate_change'] >= 0 else 'negative-saving'
    m.update(csrf(request))

    return render(request, 'progress.html', m)

@permission_required()
def progress_data_view(request, system_code=None):
    systems = System.get_systems_within_root(system_code)
    result = __calculate_progress_data(systems)
    del result['first_day_record']

    return Utils.json_response(result)
