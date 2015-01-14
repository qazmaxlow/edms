import copy, datetime, pytz
import json
import time

from django.db.models import Q
from django.core.context_processors import csrf
from django.shortcuts import render
from django.utils import timezone

from egauge.manager import SourceManager
from egauge.models import SourceReadingMonth, SourceReadingDay, SourceReadingHour
from system.models import System
from unit.models import UnitRate, CO2_CATEGORY_CODE, MONEY_CATEGORY_CODE
from utils import calculation
from utils.utils import Utils


# oops! change to write better API later
from entrak.report_views import __generate_report_data


def popup_report_view(request, system_code, year, month):
    systems_info = System.get_systems_info(system_code, request.user.system.code)
    systems = systems_info['systems']
    current_system = System.objects.get(code=system_code)
    sources = SourceManager.get_sources(current_system)

    current_system_tz = pytz.timezone(current_system.timezone)
    first_record = min([system.first_record for system in systems])
    first_record = first_record.astimezone(current_system_tz).replace(
        hour=0, minute=0, second=0, microsecond=0)
    if first_record.day == 1:
        start_dt = first_record
    else:
        start_dt = Utils.add_month(first_record, 1).replace(day=1)

    end_dt = pytz.utc.localize(datetime.datetime.utcnow()).astimezone(current_system_tz)
    end_dt = end_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    source_ids = [str(source.id) for source in sources]
    source_readings = SourceManager.get_readings_with_target_class(source_ids, SourceReadingMonth, start_dt, end_dt)
    energy_usages = calculation.combine_readings_by_timestamp(source_readings)

    unit_rates = UnitRate.objects.filter(Q(category_code=CO2_CATEGORY_CODE) | Q(category_code=MONEY_CATEGORY_CODE))
    co2_unit_rates = [unit_rate for unit_rate in unit_rates if unit_rate.category_code == CO2_CATEGORY_CODE]
    money_unit_rates = [unit_rate for unit_rate in unit_rates if unit_rate.category_code == MONEY_CATEGORY_CODE]

    co2_usages = copy.deepcopy(source_readings)
    calculation.transform_source_readings(co2_usages, systems, sources, co2_unit_rates, CO2_CATEGORY_CODE)
    co2_usages = calculation.combine_readings_by_timestamp(co2_usages)

    money_usages = copy.deepcopy(source_readings)
    calculation.transform_source_readings(money_usages, systems, sources, money_unit_rates, MONEY_CATEGORY_CODE)
    money_usages = calculation.combine_readings_by_timestamp(money_usages)

    monthly_summary = []
    for timestamp, usage in energy_usages.items():
        monthly_summary.append({
            'dt': Utils.utc_dt_from_utc_timestamp(timestamp).astimezone(current_system_tz),
            'timestamp': timestamp,
            'energy_usage': usage, 'co2_usage': co2_usages[timestamp],
            'money_usage': money_usages[timestamp]})

    m = {}
    m["monthly_summary"] = sorted(monthly_summary, key=lambda x: x['timestamp'], reverse=True)
    m.update(csrf(request))
    # oops!
    m['company_system'] = systems.first()
    report_date = datetime.datetime.strptime(year+month, '%Y%b')
    report_date = timezone.make_aware(report_date, timezone.get_current_timezone())

    try:
        next_month_date = report_date.replace(month=report_date.month+1)
    except ValueError:
        if report_date.month == 12:
            next_month_date = report_date.replace(year=report_date.year+1, month=1)
        else:
            # next month is too short to have "same date"
            # pick your own heuristic, or re-raise the exception:
            raise

    m['report_date'] = datetime.datetime.strptime(year+month, '%Y%b')
    sources = SourceManager.get_sources(current_system)
    source_ids = [str(source.id) for source in sources]

    energy_usages = calculation.combine_readings_by_timestamp(source_readings)
    readings = SourceReadingMonth.objects(
        source_id__in=source_ids,
        datetime__gte=report_date,
        datetime__lt=next_month_date
    )
    total_energy = sum([ r.value for r in readings])

    m['total_energy'] = total_energy
    m['report_start'] = report_date
    m['report_end'] = next_month_date

    # oops! monkey code
    report_data = __generate_report_data(systems, 'month',
                                  time.mktime(report_date.utctimetuple()),
                                  time.mktime(next_month_date.utctimetuple())
    )
    group_data = report_data['groupedSourceInfos']
    weekday_average = sum([ g['currentWeekdayInfo']['average'] for g in group_data])
    m['weekday_average'] = weekday_average

    unit_infos = json.loads(m['company_system'].unit_info)
    money_unit_code = unit_infos['money']
    money_unit_rate = UnitRate.objects.get(category_code='money', code=unit_infos['money'])

    m['weekday_bill'] = weekday_average * money_unit_rate.rate

    m['total_co2'] = sum([g['currentTotalCo2'] for g in group_data])/1000.0
    m['total_money'] = sum([g['currentTotalMoney'] for g in group_data])


    # useful?
    current_total = report_data['sumUpUsages'][0]
    last_total = report_data['sumUpUsages'][1]
    compare_to_last_month = None

    if last_total > 0:
        compare_to_last_month = (current_total-last_total)/last_total*100

    m['compare_to_last_month'] = compare_to_last_month

    # _fillInComparePercent = function(eleSel, oldUsage, newUsage, compareToDateText)
    # var usagePercent = (oldUsage-newUsage)/oldUsage*100;

    # beginning is for last month
    # this._fillInComparePercent(targetSel+" .compare-beginning", beginningUsage, averageUsage, beginningDateText);
    # this._fillInComparePercent(targetSel+" .compare-last", lastUsage, averageUsage, this.multiLangTexts.last_week);
    # this._fillInComparePercent(targetSel+" .compare-last-same-period", lastSamePeriodUsage, averageUsage, this.multiLangTexts.samePeriodLastYear);
    beginning_usage = sum([ g['beginningWeekdayInfo']['average'] for g in group_data])
    average_usage = sum([ g['currentWeekdayInfo']['average'] for g in group_data])
    weekday_compare_last_month = (beginning_usage - average_usage)/beginning_usage*100
    m['weekday_compare_last_month'] = weekday_compare_last_month

    last_same_period = sum([ g['lastSamePeriodWeekdayInfo']['average'] for g in group_data])
    weekday_compare_same_period = (last_same_period - average_usage)/last_same_period*100
    m['weekday_compare_same_period'] = weekday_compare_same_period

    for g in group_data:
        g['system'] = System.objects.get(code=g['systemCode'])
        g['usage'] = g['currentWeekdayInfo']['average']
        beginning_usage = g['beginningWeekdayInfo']['average']
        average_usage = g['currentWeekdayInfo']['average']

        unit_infos = json.loads(g['system'].unit_info)
        money_unit_code = unit_infos['money']
        money_unit_rate = UnitRate.objects.get(category_code='money', code=unit_infos['money'])

        g['usage_bill'] = g['usage'] * money_unit_rate.rate


        compare_last_month = None
        if beginning_usage > 0:
            compare_last_month = (beginning_usage - average_usage)/beginning_usage*100

        g['compare_last_month'] = compare_last_month

        compare_same_period = None
        last_same_period = g['lastSamePeriodWeekdayInfo']['average']
        if last_same_period > 0:
            compare_same_period = (last_same_period - average_usage)/last_same_period*100

        g['compare_same_period'] = compare_same_period
        g['diff_same_period'] = last_same_period - average_usage

    combined_readings = {}
    for g in group_data:
        current_readings = g['currentReadings']
        for ts, val in current_readings.items():
            if ts in combined_readings:
                combined_readings[ts] += val
            else:
                combined_readings[ts] = val


    highest_datetime, highest_usage= sorted(combined_readings.items(), key=lambda x: x[1])[-1]
    # m['highest_value']
    groupdata_sorted_by_diff = sorted(group_data, key=lambda x: x['diff_same_period'])
    highest_diff_source = groupdata_sorted_by_diff[-1]
    m['highest_diff_source'] = highest_diff_source

    m['weekday_highest_usage'] = highest_usage
    m['weekday_highest_datetime'] = datetime.datetime.fromtimestamp(highest_datetime, pytz.utc)

    m['weekday_details'] = group_data
    m['saving_info'] = report_data['savingInfo']
    m['saving_energy'] = -1 * report_data['savingInfo']['energy']
    # in tons
    m['saving_co2'] = -1 * report_data['savingInfo']['co2'] / 1000.0
    m['saving_money'] = -1 * report_data['savingInfo']['money']

    m['co2_in_car'] = abs(report_data['savingInfo']['co2']*0.003)
    m['co2_in_forest'] = abs(report_data['savingInfo']['co2']*0.016)
    m['co2_in_elephant'] = abs(report_data['savingInfo']['co2']*0.00667)
    # var co2InCar = Utils.formatWithCommas(Math.abs((reportGenThis.savingInfo.co2*0.003).toFixed(0)));

    # lastSamePeriodUsage += info[lastSamePeriodUsageKey].average;

    # this.generateCalendarReport('#weekday-info', combinedReadings,
    #     'currentWeekdayInfo', 'beginningWeekdayInfo',
    #     'lastWeekdayInfo', 'lastSamePeriodWeekdayInfo', lowestUsage, lowestDt, highestUsage, highestDt,
    #     false, isNotConcernFunc, 'weekday-sub-calendar', this.multiLangTexts.calendarTypeWeekday,
    #     this.multiLangTexts.calendarSplitWeekdays, this.multiLangTexts.calendarSplitWeekends);


    return render(request, 'companies/reports/popup_report.html', m)

