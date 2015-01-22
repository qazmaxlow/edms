import copy, datetime, pytz
import json
import time

from django.db.models import Q
from django.core.context_processors import csrf
from django.core.serializers.json import DjangoJSONEncoder
from django.shortcuts import render
from django.utils import timezone

from egauge.manager import SourceManager
from egauge.models import SourceReadingMonth, SourceReadingDay, SourceReadingHour, Source
from system.models import System
from unit.models import UnitRate, CO2_CATEGORY_CODE, MONEY_CATEGORY_CODE
from utils import calculation
from utils.utils import Utils


# oops! change to write better API later
from entrak.report_views import __generate_report_data


def previous_month(datetime):
    try:
        previous_month_date = datetime.replace(month=datetime.month-1)
    except ValueError:
        if datetime.month == 1:
            previous_month_date = datetime.replace(year=datetime.year-1, month=12)
        else:
            raise

    return previous_month_date


def next_month(datetime):
    try:
        next_month_date = datetime.replace(month=datetime.month+1)
    except ValueError:
        if datetime.month == 12:
            next_month_date = datetime.replace(year=datetime.year+1, month=1)
        else:
            # next month is too short to have "same date"
            # pick your own heuristic, or re-raise the exception:
            raise

    return next_month_date


def report_view(request, system_code=None):
    systems_info = System.get_systems_info(system_code, request.user.system.code)
    systems = systems_info['systems']
    current_system = systems[0]
    sources = SourceManager.get_sources(current_system)

    current_system_tz = pytz.timezone(current_system.timezone)
    first_record = min([system.first_record for system in systems])
    first_record = first_record.astimezone(current_system_tz).replace(
        hour=0, minute=0, second=0, microsecond=0)
    if first_record.day == 1:
        start_dt = first_record
    else:
        start_dt = Utils.add_month(first_record, 1).replace(day=1)

    # should use system timezone
    start_dt = datetime.datetime.now(current_system_tz)
    start_dt = start_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    # start_dt = previous_month(start_dt)
    start_dt = previous_month(start_dt)

    # end_dt = pytz.utc.localize(datetime.datetime.utcnow()).astimezone(current_system_tz)
    end_dt = datetime.datetime.now(current_system_tz)
    end_dt = end_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    source_ids = [str(source.id) for source in sources]
    source_readings = SourceManager.get_readings_with_target_class(source_ids, SourceReadingMonth, start_dt, end_dt)

    last_month_start_dt = previous_month(start_dt)
    last_month_end_dt = previous_month(end_dt)
    last_month_source_readings = SourceManager.get_readings_with_target_class(source_ids, SourceReadingMonth, last_month_start_dt, last_month_end_dt)

    energy_usages = calculation.combine_readings_by_timestamp(source_readings)

    unit_rates = UnitRate.objects.filter(Q(category_code=CO2_CATEGORY_CODE) | Q(category_code=MONEY_CATEGORY_CODE))
    co2_unit_rates = [unit_rate for unit_rate in unit_rates if unit_rate.category_code == CO2_CATEGORY_CODE]
    money_unit_rates = [unit_rate for unit_rate in unit_rates if unit_rate.category_code == MONEY_CATEGORY_CODE]

    monthly_energy_sum = sum([sr.values()[0] for sr in source_readings.values()])

    # unit_infos = json.loads(current_system.unit_info)
    # money_unit_code = unit_infos['money']
    # _money_unit_rates = UnitRate.objects.filter(category_code='money', code=unit_infos['money'])

    source_timestamp_energy = [(source_id, ) + sr.items()[0] for source_id, sr in source_readings.items()]
    # assert False

    def get_unit_rate(source_id, timestamp):
        source = Source.objects(id=str(source_id)).first()
        # assert False
        system = System.objects.get(code=source.system_code)
        unit_infos = json.loads(system.unit_info)
        money_unit_code = unit_infos['money']
        money_unit_rates = UnitRate.objects.filter(category_code='money', code=unit_infos['money'])
        dt = datetime.datetime.fromtimestamp(timestamp, pytz.utc)
        ur = money_unit_rates.filter(effective_date__lte=dt).order_by('-effective_date').first()
        return ur

    monthly_money_sum = sum([ get_unit_rate(s, t).rate*e for s, t, e in source_timestamp_energy])

    # ds = [ datetime.datetime.fromtimestamp(t) for t, e in timestamp_energy]

    co2_usages = copy.deepcopy(source_readings)
    calculation.transform_source_readings(co2_usages, systems, sources, co2_unit_rates, CO2_CATEGORY_CODE)
    co2_usages = calculation.combine_readings_by_timestamp(co2_usages)

    money_usages = copy.deepcopy(source_readings)
    # [63.25035888888888, 82.13227444444445, 194.7879794444444, 16.041575555555553, 245.49638694444442, 1085.012150833333]
    calculation.transform_source_readings(money_usages, systems, sources, money_unit_rates, MONEY_CATEGORY_CODE)
    # assert False
    money_usages = calculation.combine_readings_by_timestamp(money_usages)



    monthly_summary = []
    for timestamp, usage in energy_usages.items():
        monthly_summary.append({
            'dt': Utils.utc_dt_from_utc_timestamp(timestamp).astimezone(current_system_tz),
            'timestamp': timestamp,
            'energy_usage': usage, 'co2_usage': co2_usages[timestamp],
            'money_usage': money_usages[timestamp]})

    m = systems_info
    m["monthly_summary"] = sorted(monthly_summary, key=lambda x: x['timestamp'], reverse=True)
    m['month_summary'] = monthly_summary[0]
    m.update(csrf(request))

    current_month_money = m['month_summary']['money_usage']
    calculation.transform_source_readings(last_month_source_readings, systems, sources, money_unit_rates, MONEY_CATEGORY_CODE)
    last_month_money_usages = calculation.combine_readings_by_timestamp(last_month_source_readings)
    last_month_money_usage = last_month_money_usages.values()[0] if last_month_money_usages else 0

    compare_last_month_money = (current_month_money - last_month_money_usage)/ current_month_money * 100
    m['compare_last_month_money'] = compare_last_month_money
    m['monthly_money_sum'] = monthly_money_sum

    return render(request, 'companies/reports/summary.html', m)


class CompareTplHepler:
    def __init__(self, compared_percent):
        self.compared_percent = compared_percent

    @property
    def compared_percent_abs(self):
        return abs(self.compared_percent)

    @property
    def change_desc(self):
        return 'more' if self.compared_percent >=0 else 'less'

    @property
    def change_css_class(self):
        return 'more-usage' if self.compared_percent >=0 else 'less-usage'

    @property
    def change_icon_path(self):
        path = 'images/reports/decrease_engry.svg'
        if self.compared_percent >=0:
            path = 'images/reports/increase_engry.svg'

        return path

    @property
    def text_desc(self):
        return "{self.compared_percent_abs:.0f}% {self.change_desc}".format(self=self)


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
    # oops, wrong?
    money_unit_rate = UnitRate.objects.filter(category_code='money', code=unit_infos['money']).first()

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
    weekday_compare_last_month = None
    if beginning_usage > 0:
        weekday_compare_last_month = (beginning_usage - average_usage)/beginning_usage*100
    # m['weekday_compare_last_month'] = weekday_compare_last_month
    m['weekday_month_compare_helper'] = CompareTplHepler(weekday_compare_last_month)

    last_same_period = sum([ g['lastSamePeriodWeekdayInfo']['average'] for g in group_data])

    weekday_compare_same_period = None
    if last_same_period > 0 :
        weekday_compare_same_period = (last_same_period - average_usage)/last_same_period*100

    m['weekday_compare_same_period'] = weekday_compare_same_period
    m['weekday_same_period_compare_helper'] = CompareTplHepler(weekday_compare_same_period)

    for g in group_data:
        g['system'] = System.objects.get(code=g['systemCode'])
        g['usage'] = g['currentWeekdayInfo']['average']
        beginning_usage = g['beginningWeekdayInfo']['average']
        average_usage = g['currentWeekdayInfo']['average']

        unit_infos = json.loads(g['system'].unit_info)
        money_unit_code = unit_infos['money']
        money_unit_rate = UnitRate.objects.filter(category_code='money', code=unit_infos['money']).first()

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

    # this is combined current readings
    combined_readings = {}

    # combined_current_readings = {};
    combined_last_readings = {};
    for g in group_data:
        current_readings = g['currentReadings']
        g['compare_last_month_helper'] = CompareTplHepler(g['compare_last_month'])
        g['compare_same_period_helper'] = CompareTplHepler(g['compare_same_period'])
        for ts, val in current_readings.items():
            if ts in combined_readings:
                combined_readings[ts] += val
            else:
                combined_readings[ts] = val

        last_readings = g['lastReadings']
        for ts, val in last_readings.items():
            if ts in combined_last_readings:
                combined_last_readings[ts] += val
            else:
                combined_last_readings[ts] = val

    # m['combined_current_readings'] = combined_readings
    # m['combined_last_readings'] = combined_last_readings
    # compare current series
    # compare_current_readings_series = []
    # for ts, val in combined_readings.items():
    #     compare_current_readings_series.append(
    #         {
    #             'date': datetime.datetime.fromtimestamp(ts, pytz.utc),
    #             'value': val
    #         }
    #     )

    m['compare_current_readings_series']= json.dumps(combined_readings.values(), cls=DjangoJSONEncoder)
    m['compare_current_readings_month'] = report_date.strftime('%b')

    m['compare_last_readings_series']= json.dumps(combined_last_readings.values(), cls=DjangoJSONEncoder)

    m['compare_last_readings_month'] = previous_month(report_date).strftime('%b')
    # assert False


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
    m['css_class_energy_saving'] = 'positive-saving' if report_data['savingInfo']['energy'] >=0 else 'negative-saving'
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

    transformed_datas = []
    energy_percentsum = 0

    for g in group_data:
        change_in_kwh = (g['currentTotalMoney'] - g['last_year_this_month']['money'])/g['last_year_this_month']['money'] * 100 if g['last_year_this_month']['money'] > 0 else None
        data_info = {
            'total_energy': g['currentTotalEnergy'],
            'co2_val': g['currentTotalCo2'],
            'money_val': g['currentTotalMoney'],
            'change_in_kwh': change_in_kwh,
            'change_in_money': g['currentTotalMoney']- g['last_year_this_month']['money'] if g['last_year_this_month']['money'] else None
        }

        data_info['name'] = g['sourceNameInfo']['en'] if g['systemCode'] == m['company_system'].code else g['system'].fullname

        if g is not group_data[-1]:
            data_info['energy_percent'] = g['currentTotalEnergy']/total_energy*100
            energy_percentsum += data_info['energy_percent']
        else:
            data_info['energy_percent'] = 100 - energy_percentsum

        transformed_datas.append(data_info)

    m['transformed_datas'] = transformed_datas
    # var transformedDatas = [];
    # var energyPercentSum = 0;
    # $.each(reportGenThis.groupedSourceInfos, function(infoIdx, info) {
    #     var change_in_kwh = (info.last_year_this_month.money > 0) ? (info.currentTotalMoney-info.last_year_this_month.money)/info.last_year_this_month.money*100 : 'N/A';
    #     var dataInfo = {
    #         totalEnergy: info.currentTotalEnergy,
    #         co2Val: info.currentTotalCo2,
    #         moneyVal: info.currentTotalMoney,
    #         change_in_kwh: change_in_kwh,
    #         change_in_money: (info.last_year_this_month.money > 0) ? info.currentTotalMoney-info.last_year_this_month.money : 'N/A'
    #     };
    #     dataInfo.name = (info.systemCode === reportGenThis.systemTree.data.code) ? info.sourceNameInfo[reportGenThis.langCode] : info.system.data.nameInfo[reportGenThis.langCode];
    #     if (infoIdx < reportGenThis.groupedSourceInfos.length-1) {
    #         dataInfo.energyPercent = parseFloat(Utils.fixedDecBaseOnVal((info.currentTotalEnergy/totalEnergyUsage)*100));
    #         energyPercentSum += dataInfo.energyPercent;
    #     } else {
    #         dataInfo.energyPercent = parseFloat(Utils.fixedDecBaseOnVal(100-energyPercentSum));
    #     }
    #     transformedDatas.push(dataInfo);
    # });
    m['sum_up_usages'] = report_data['sumUpUsages']
    # max_sum_up = max(report_data['sumUpUsages'])
    sumup_usages = report_data['sumUpUsages']

    # make 6 months
    # report_date
    # compare_past
    compare_past_date = report_date
    # for i in range(6):

    compare_past_datasource = []
    for su in sumup_usages:
        compare_past_datasource.append({
            'value': su,
            'month': compare_past_date.strftime('%b'), 'country': "us"})
        compare_past_date = previous_month(compare_past_date)
    compare_past_datasource.reverse()

    # oops, hack?
    m['compare_past_datasource_json'] = json.dumps(compare_past_datasource)

    # weekends
    m['weekends'] = {}
    m['weekends']['a'] = 1


    return render(request, 'companies/reports/popup_report.html', m)


# @permission_required()
def download_report_view(request, system_code, start_timestamp, end_timestamp, report_type, report_layout=None):
    # start_timestamp = request.POST.get("start_timestamp")
    # end_timestamp = request.POST.get("end_timestamp", 0)
    # report_type = request.POST.get("report_type")
    # report_layout = request.POST.get('report_layout')
    # assert False

    if request.is_secure():
        domain_url = "https://" + request.META['HTTP_HOST']
    else:
        domain_url = "http://" + request.META['HTTP_HOST']

    # assert False
    report_name = 'generate_report_pdf'
    # if report_layout == 'summary':
    #     report_name = 'generate_summary_report_pdf'

    request_url = domain_url + reverse(report_name, kwargs={
        'system_code': system_code,
        'report_type': report_type,
        'start_timestamp': start_timestamp,
        'end_timestamp': end_timestamp,
        'lang_code': translation.get_language()
    })

    report_pdf_name = datetime.datetime.now().strftime("%Y%m%d")
    report_pdf_name += "-" + uuid.uuid4().hex[:10] + ".pdf"
    report_pdf_path = os.path.join(TEMP_MEDIA_DIR, report_pdf_name)
    pdf_options = {
        "javascript-delay": '3000',
        'quiet': '',
        'margin-left': '18mm',
        'page-size': 'A3',
    }
    pdfkit.from_url(request_url, report_pdf_path, options=pdf_options)

    with open(report_pdf_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="report.pdf"'
    os.remove(report_pdf_path)

    return response
