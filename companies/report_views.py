from bson.objectid import ObjectId
import copy, datetime, pytz
import json
from mongoengine import connection, Q as MQ
import operator
import time
from dateutil.relativedelta import relativedelta

from django.db.models import Q
from django.core.context_processors import csrf
from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.shortcuts import render
from django.templatetags.static import static
from django.utils import timezone, dateparse, translation
from django.utils import formats
from django.utils.translation import ugettext as _
from django.utils.dateformat import DateFormat

from wkhtmltopdf.views import PDFTemplateResponse

from egauge.manager import SourceManager
from egauge.models import SourceReadingYear, SourceReadingMonth, SourceReadingDay, SourceReadingHour, SourceReadingMin, Source
from system.models import System
from unit.models import UnitRate, CO2_CATEGORY_CODE, MONEY_CATEGORY_CODE
from utils.auth import permission_required
from utils import calculation
from utils.utils import Utils


# oops! change to write better API later
from entrak.report_views import __generate_report_data
from django.conf.global_settings import LANGUAGE_CODE


def current_lang():
    if (translation.get_language()=="zh-tw"):
        return "zh-tw"
    return "en"

def get_source_name(source_id):
    source = Source.objects(id=str(source_id)).first()
    if (current_lang()=="zh-tw"):
        return source.d_name_tc
    return source.d_name

def get_unitrate(source_id, datetime):
    source = Source.objects(id=str(source_id)).first()
    system = System.objects.get(code=source.system_code)
    unit_infos = json.loads(system.unit_info)
    money_unit_code = unit_infos['money']
    money_unit_rates = UnitRate.objects.filter(category_code='money', code=unit_infos['money'])
    dt = datetime
    ur = money_unit_rates.filter(effective_date__lte=dt).order_by('-effective_date').first()
    return ur


def get_unitrate_by_system(system, datetime):
    unit_infos = json.loads(system.unit_info)
    money_unit_code = unit_infos['money']
    money_unit_rates = UnitRate.objects.filter(category_code='money', code=unit_infos['money'])
    dt = datetime
    ur = money_unit_rates.filter(effective_date__lte=dt).order_by('-effective_date').first()
    return ur


def get_total_cost(source_ids, start_dt, end_dt, date_type):
    reading_map = {
        'week': SourceReadingDay,
        'month': SourceReadingMonth,
        'quarter': SourceReadingMonth,
        'year': SourceReadingYear,
        'custom': SourceReadingDay
    }

    reading_cls = reading_map[date_type]

    month_readings = reading_cls.objects(
        source_id__in=source_ids,
        datetime__gte=start_dt,
        datetime__lt=end_dt)

    if month_readings:
        return sum([get_unitrate(r.source_id, r.datetime).rate*r.value for r in month_readings])


def get_weekdays_cost_by_source_readings(system, source_id, start_dt, end_dt):
    all_holidays = system.get_all_holidays()
    total_day = 0
    total_val = 0

    readings = SourceReadingDay.objects(
        source_id=source_id,
        datetime__gte=start_dt,
        datetime__lte=end_dt)

    system_tz = pytz.timezone(system.timezone)
    for sr in readings:
        source_id = sr.source_id
        dt = sr.datetime.astimezone(system_tz)

        if dt.weekday() <= 4 and (dt.date() not in all_holidays):
            total_val += get_unitrate(source_id, dt).rate * sr.value
            total_day += 1

    if total_day > 0:
        return total_val / float(total_day)


def get_weekdays_cost(system, start_dt, end_dt):
    sources = SourceManager.get_sources(system)
    source_ids = [str(source.id) for source in sources]

    # group by source id
    source_groups = {}
    avgs = []

    for sid in source_ids:
        avg_cost = get_weekdays_cost_by_source_readings(system, sid, start_dt, end_dt)
        if avg_cost is not None:
            avgs.append(avg_cost)

    if avgs:
        return sum(avgs)


def get_overnight_avg_cost(system, source_ids, start_dt, end_dt):
    date_ranges = []

    unit_infos = json.loads(system.unit_info)
    # money_unit_code = unit_infos['money']
    # money_unit_rate = UnitRate.objects.filter(category_code='money', code=unit_infos['money']).first()
    money_unit_rates = UnitRate.objects.filter(category_code='money', code=unit_infos['money']).order_by('effective_date')
    system_tz = pytz.timezone(system.timezone)

    for ix, mr in enumerate(money_unit_rates):
        c_rate_date = mr.effective_date.astimezone(system_tz)
        if c_rate_date >= start_dt and c_rate_date < end_dt:
            try:
                n_rate_date = money_unit_rates[ix+1].effective_date.astimezone(system_tz)
                if n_rate_date > end_dt:
                    n_rate_date = end_dt

                date_range = (c_rate_date, n_rate_date, mr)
                date_ranges.append(date_range)
            except IndexError:
                date_range = (c_rate_date, end_dt, mr)
                date_ranges.append(date_range)

    # if no date ranges use the first rate as the default money rate
    # else if first date range has gap between the start date
    # use the first money_unit_rate as the default unit rate
    if not date_ranges:
        default_rate = money_unit_rates.first()
        date_range = (start_dt, end_dt, default_rate)
        date_ranges.append(date_range)
    elif start_dt < date_ranges[0][0]:
        default_rate = money_unit_rates.first()
        date_range = (start_dt, date_ranges[0][0], default_rate)
        date_ranges.append(date_range)

    total_on_sum = 0
    for date_range in date_ranges:
        sd, ed, r = date_range
        mqs = []
        num_day = (ed - sd).days
        rdays = [sd+datetime.timedelta(days=n) for n in range(num_day)]
        for rday in rdays:
            on_sd = datetime.datetime.combine(rday, system.night_time_start)
            on_sd = on_sd.replace(tzinfo=system_tz)

            on_ed = datetime.datetime.combine(
                rday + datetime.timedelta(days=1), system.night_time_end)
            on_ed = on_ed.replace(tzinfo=system_tz)

            q = MQ(datetime__gte=on_sd, datetime__lt=on_ed)
            mqs.append(q)

        conds = reduce(
            operator.or_,
            mqs
        )

        dr_sum = r.rate * SourceReadingHour.objects(conds, source_id__in=source_ids).sum('value')
        total_on_sum += dr_sum

    # dirty way to count number of days
    total_day = (end_dt - start_dt).days
    today = datetime.datetime.now(pytz.utc)
    if end_dt > today:
        total_day = (today - start_dt).days

    return total_on_sum / total_day


@permission_required()
def summary_ajax(request, system_code):
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


    sd = request.GET.get('start_date')
    if sd:
        start_dt = dateparse.parse_date(request.GET.get('start_date'))
        start_dt = datetime.datetime.combine(start_dt, datetime.datetime.min.time())
        start_dt = current_system_tz.localize(start_dt)


    ed = request.GET.get('end_date')
    if ed:
        end_dt = dateparse.parse_date(ed)
        end_dt = datetime.datetime.combine(end_dt, datetime.datetime.min.time())
        end_dt = current_system_tz.localize(end_dt)

    source_ids = [str(source.id) for source in sources]
    all_holidays = current_system.get_all_holidays()

    # end_dt is at time 00:00:00 which excluded the last day
    # add 1 more day to end_dt for actual calculation
    end_dt = end_dt + relativedelta(days=1)
    day_source_readings = SourceManager.get_readings_with_target_class(source_ids, SourceReadingDay, start_dt, end_dt)


    compare_type = request.GET.get('compare_type')
    total_cost = get_total_cost(source_ids, start_dt, end_dt, compare_type)
    print(total_cost)

    if compare_type == 'month':
        last_start_dt = start_dt - relativedelta(months=1)
        last_end_dt = end_dt - relativedelta(months=1)
    elif compare_type == 'week':
        last_start_dt = start_dt - datetime.timedelta(days=7)
        last_end_dt = end_dt - datetime.timedelta(days=7)
    elif compare_type == 'quarter':
        last_start_dt = start_dt - relativedelta(months=3)
        last_end_dt = end_dt - relativedelta(months=3)
    elif compare_type == 'year':
        last_start_dt = start_dt - relativedelta(years=1)
        last_end_dt = end_dt - relativedelta(years=1)
    elif compare_type == 'custom':
        date_delta = end_dt - start_dt
        last_end_dt = start_dt - datetime.timedelta(days=1)
        last_start_dt = last_end_dt - date_delta

    last_total_cost = get_total_cost(source_ids, last_start_dt, last_end_dt, compare_type)

    compare_to_last_total = None

    if last_total_cost > 0 and total_cost:
        compare_to_last_total = float(total_cost-last_total_cost)/last_total_cost*100


    # weekday
    def weekday_cost_avg(source_id, source_reading):

        total_day = 0
        total_val = 0

        all_datetimes = [datetime.datetime.fromtimestamp(t, current_system_tz) for t,v in source_reading.items()]

        for t, v in source_reading.items():
            dt = datetime.datetime.fromtimestamp(t, current_system_tz)
            if dt.weekday() <= 4 and dt.date() not in all_holidays:
                total_val += get_unitrate(source_id, dt).rate * v
                total_day += 1

        if total_day > 0:
            return total_val / float(total_day)

    def _get_weekdays_cost(source_ids, start_dt, end_dt):
        day_source_readings = SourceManager.get_readings_with_target_class(source_ids, SourceReadingDay, start_dt, end_dt)
        if day_source_readings:
            weekday_costs = [(source_id, weekday_cost_avg(source_id, sr) ) for source_id, sr in day_source_readings.items()]
            return sum([ c for s, c in weekday_costs if c is not None])


    weekday_cost = get_weekdays_cost(current_system, start_dt, end_dt)
    # weekday_money_sum = sum([ c for s, c in weekday_costs if c is not None])

    compare_to_last_weekdays = None

    last_weekdays_cost = get_weekdays_cost(current_system, last_start_dt, last_end_dt)

    if last_weekdays_cost > 0 and weekday_cost:
        compare_to_last_weekdays = float(weekday_cost-last_weekdays_cost)/last_weekdays_cost*100

    # m = systems_info
    m = {}

    m['formated_total_cost'] = '${0:,.0f}'.format(total_cost) if total_cost is not None else None
    m['formated_weekday_cost'] = '${0:,.0f}'.format(weekday_cost) if weekday_cost is not None else None

    m['compare_to_last_total'] = CompareTplHepler(compare_to_last_total).to_dict()
    m['compare_to_last_weekdays'] = CompareTplHepler(compare_to_last_weekdays).to_dict()

    # overnight
    def overnight_cost(reading):
        # just ensure tz_aware=true in mongo connect
        dt = reading.datetime.astimezone(current_system_tz)

        if dt.time() >= current_system.night_time_start or \
           dt.time() < current_system.night_time_end:
            # total_val += get_unit_rate(source_id, t).rate * v
            return get_unitrate(reading.source_id, reading.datetime).rate * reading.value


    def _get_overnight_avg_cost(source_ids, start_dt, end_dt):
        overnight_start = datetime.datetime.combine(start_dt, datetime.datetime.min.time())
        overnight_start= current_system_tz.localize(overnight_start)

        overnight_end =  datetime.datetime.combine(end_dt, current_system.night_time_start)
        overnight_end = current_system_tz.localize(overnight_end)

        overnight_readings = SourceReadingHour.objects(
            source_id__in=source_ids,
            datetime__gte=overnight_start,
            datetime__lt=overnight_end)


        total_days = (end_dt - start_dt).days
        # group might get issue?
        # group_overnight_readings = SourceManager.group_readings_with_source_id(overnight_readings)

        overnight_costs = [overnight_cost(r) for r in overnight_readings if overnight_cost(r) is not None]
        if overnight_costs:
            return sum([ c for c in overnight_costs if c is not None])/total_days

    # source = Source.objects(id=str(source_id)).first()
    # system = System.objects.get(code=source.system_code)
    unit_infos = json.loads(current_system.unit_info)
    money_unit_code = unit_infos['money']
    money_unit_rates = UnitRate.objects.filter(category_code='money', code=unit_infos['money']).order_by('effective_date')



    overnight_avg_cost = get_overnight_avg_cost(current_system, source_ids, start_dt, end_dt)
    # overnight_avg_cost = total_on_sum / (end_dt - start_dt).days
    # overnight_avg_cost = get_overnight_avg_cost(source_ids, start_dt, end_dt)
    m['formated_overnight_avg_cost'] = '${0:,.0f}'.format(overnight_avg_cost) if overnight_avg_cost else None

    compare_to_last_overnight_avg_cost = None
    last_overnight_avg_cost = get_overnight_avg_cost(current_system, source_ids, last_start_dt, last_end_dt)

    if last_overnight_avg_cost > 0 and overnight_avg_cost is not None:
        compare_to_last_overnight_avg_cost = float(overnight_avg_cost-last_overnight_avg_cost)/last_overnight_avg_cost*100
    m['compare_to_last_overnight_avg_cost'] = CompareTplHepler(compare_to_last_overnight_avg_cost).to_dict()

    data = m

    return HttpResponse(json.dumps(data, cls=DjangoJSONEncoder), content_type="application/json")


@permission_required()
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
    start_dt = start_dt - relativedelta(months=1)

    # end_dt = pytz.utc.localize(datetime.datetime.utcnow()).astimezone(current_system_tz)
    end_dt = datetime.datetime.now(current_system_tz)
    end_dt = end_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    source_ids = [str(source.id) for source in sources]
    source_readings = SourceManager.get_readings_with_target_class(source_ids, SourceReadingMonth, start_dt, end_dt)

    last_month_start_dt = start_dt - relativedelta(months=1)
    last_month_end_dt = end_dt - relativedelta(months=1)
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
    m['month_summary'] = monthly_summary[0] if monthly_summary else None
    m.update(csrf(request))

    if m['month_summary']:
        current_month_money = m['month_summary']['money_usage']
        calculation.transform_source_readings(last_month_source_readings, systems, sources, money_unit_rates, MONEY_CATEGORY_CODE)
        last_month_money_usages = calculation.combine_readings_by_timestamp(last_month_source_readings)
        last_month_money_usage = last_month_money_usages.values()[0] if last_month_money_usages else 0

        compare_last_month_money = float(current_month_money - last_month_money_usage)/ current_month_money * 100
        m['compare_last_month_money'] = compare_last_month_money
        m['monthly_money_sum'] = monthly_money_sum

    m['default_date'] = start_dt
    m['today_date'] = datetime.datetime.now(pytz.utc)
    m['default_custom_end_date'] = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=1)
    m['default_custom_start_date'] = m['default_custom_end_date'] - datetime.timedelta(days=30)
    # return render(request, 'testing_code.html', m)
    return render(request, 'companies/reports/summary.html', m)


class CompareTplHepler:
    def __init__(self, compared_percent):
        self.compared_percent = compared_percent

    @property
    def compared_percent_abs(self):
        return abs(self.compared_percent) if self.compared_percent else None

    @property
    def formated_percent_change(self):
        return _('{0:.0f}% {1}').format(self.compared_percent_abs, self.change_desc) if self.compared_percent is not None else None

    @property
    def change_desc(self):
        return _('more') if self.compared_percent >=0 else _('less')

    @property
    def change_css_class(self):
        return 'more-usage' if self.compared_percent >=0 else 'less-usage'

    @property
    def change_icon_path(self):
        if self.compared_percent is None:
            return 'images/reports/na.gif'

        path = 'images/reports/decrease_energy.png'
        if self.compared_percent >=0:
            path = 'images/reports/increase_energy.png'

        return path

    @property
    def text_desc(self):
        if self.compared_percent_abs:
            return _("{self.compared_percent_abs:.0f}% {self.change_desc}").format(self=self)
        else:
            return 'N/A'

    def to_dict(self):
        return {
            'percent': self.compared_percent,
            'percent_abs': self.compared_percent_abs,
            'formated_percent_change': self.formated_percent_change,
            'desc': self.change_desc,
            'css_class': self.change_css_class,
            'icon_path': static(self.change_icon_path)
        }


def _popup_report_view(request, system_code, year=None, month=None, report_type=None, to_pdf=False):
    systems_info = System.get_systems_info(system_code, request.user.system.code)
    systems = systems_info['systems']
    current_system = System.objects.get(code=system_code)
    sources = SourceManager.get_sources(current_system)

    report_type = request.GET.get('report_type')

    type_colors = ['#68c0d4', '#8c526f', '#d5c050', '#8B8250', '#5759A7', '#6EC395', '#ee9646', '#ee5351', '#178943', '#ba1e6a', '#045a6f', '#0298bb']

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
    if year and month:
        report_date = datetime.datetime.strptime(year+month, '%Y%b')
        report_date = timezone.make_aware(report_date, timezone.get_current_timezone())
        m['report_date'] = datetime.datetime.strptime(year+month, '%Y%b')

        report_end_date = report_date + relativedelta(months=1)

    sd = request.GET.get('start_date')
    if sd:
        report_date = dateparse.parse_date(sd)
        report_date = datetime.datetime.combine(report_date, datetime.datetime.min.time())
        report_date = current_system_tz.localize(report_date)

    end_dt = start_dt + relativedelta(months=1)

    ed = request.GET.get('end_date')
    if ed:
        report_end_date = dateparse.parse_date(ed)
        report_end_date = datetime.datetime.combine(report_end_date, datetime.datetime.min.time())
        report_end_date = current_system_tz.localize(report_end_date)

    m['report_type'] = report_type
    report_type_name = report_type
    report_date_text = u"{0} - {1}".format(
        DateFormat(report_date).format("j M Y"),
        DateFormat(report_end_date).format("j M Y")
    )
    if report_type == 'month':
        report_type_name = _('month')
        report_sidebar_label = _('Compared to Last Month')
        if (current_lang()=="zh-tw"):
            report_date_text = _(u"{0}{1} - Monthly Energy Report").format(report_date.strftime("%Y"),report_date.strftime("%-m"))
        else:
            report_date_text = _(u"{0} - Monthly Energy Report").format(DateFormat(report_date).format("M Y"))
    elif report_type == 'week':
        report_type_name = _('week')
        report_sidebar_label = _('Compared to Last Week')
        if (current_lang()=="zh-tw"):
            report_date_text_begin = _(u"{0}{1}{2} - ").format(report_date.strftime("%Y"),report_date.strftime("%-m"),report_date.strftime("%-d"))
            report_date_text_end = _(u"{0}{1}{2} Weekly Energy Report").format(report_end_date.strftime("%Y"),report_end_date.strftime("%-m"),report_end_date.strftime("%-d"))
            report_date_text = report_date_text_begin + report_date_text_end
        else:
            report_date_text = _("{0} Weekly Energy Report").format(report_date_text)
    elif report_type == 'quarter':
        report_type_name = _('quarter')
        report_sidebar_label = _('Compared to Last Quarter')
        quarter_text =  _('{0} Q{1}').format(report_date.strftime("%Y"), report_end_date.month/3)
        report_date_text = _("{0} - Quarterly Energy Report").format(quarter_text)
    elif report_type == 'year':
        report_type_name = _('year')
        report_sidebar_label = _('Compared to Last Year')
        report_date_text = _("{0} - Yearly Energy Report").format(formats.date_format(report_date, 'YEAR_FORMAT'))
    if report_type =='custom':
        report_type_name = _('month')
        report_sidebar_label = _('Compared to Last Month')
        if (current_lang()=="zh-tw"):
            report_date_text_begin = _(u"{0}{1}{2} - ").format(report_date.strftime("%Y"),report_date.strftime("%-m"),report_date.strftime("%-d"))
            report_date_text_end = _(u"{0}{1}{2}").format(report_end_date.strftime("%Y"),report_end_date.strftime("%-m"),report_end_date.strftime("%-d"))
            report_date_text = report_date_text_begin + report_date_text_end
    m['report_type_name'] = report_type_name
    m['report_sidebar_label'] = report_sidebar_label
    m['report_date_text'] = report_date_text
    m['report_day_diff'] = (report_end_date - report_date).days

    sources = SourceManager.get_sources(current_system)
    source_ids = [str(source.id) for source in sources]

    energy_usages = calculation.combine_readings_by_timestamp(source_readings)

    if report_type == 'week' or report_date == 'custom':
        readings = SourceReadingHour.objects(
            source_id__in=source_ids,
            datetime__gte=report_date,
            datetime__lt=report_end_date
        )
    else:
        readings = SourceReadingMonth.objects(
            source_id__in=source_ids,
            datetime__gte=report_date,
            datetime__lt=report_end_date
        )
    total_energy = sum([ r.value for r in readings])

    m['total_energy'] = total_energy
    m['report_start'] = report_date
    m['report_end'] = report_end_date

    # oops! monkey code
    report_data_type = report_type
    if report_type == 'custom':
        report_data_type = 'custom-month'

    report_data = __generate_report_data(systems, report_data_type,
                                  time.mktime(report_date.utctimetuple()),
                                  time.mktime(report_end_date.utctimetuple())
    )

    m['report_data_json'] = json.dumps(report_data)

    group_data = report_data['groupedSourceInfos']


    unit_infos = json.loads(m['company_system'].unit_info)
    money_unit_code = unit_infos['money']
    # oops, wrong?
    money_unit_rate = UnitRate.objects.filter(category_code='money', code=unit_infos['money']).first()

    m['weekday_bill'] = get_weekdays_cost(current_system, report_date, report_end_date)

    m['total_co2'] = sum([g['currentTotalCo2'] for g in group_data])/1000.0
    m['total_money'] = sum([g['currentTotalMoney'] for g in group_data])


    # useful?
    current_total = report_data['sumUpUsages'][0]
    last_total = report_data['sumUpUsages'][1]
    compare_to_last_month = None

    if last_total > 0:
        compare_to_last_month = float(current_total-last_total)/last_total*100

    m['compare_to_last_month'] = compare_to_last_month
    m['compare_to_last_month_abs'] = abs(compare_to_last_month) if compare_to_last_month else None


    # _fillInComparePercent = function(eleSel, oldUsage, newUsage, compareToDateText)
    # var usagePercent = (oldUsage-newUsage)/oldUsage*100;

    # beginning is for last month
    # this._fillInComparePercent(targetSel+" .compare-beginning", beginningUsage, averageUsage, beginningDateText);
    # this._fillInComparePercent(targetSel+" .compare-last", lastUsage, averageUsage, this.multiLangTexts.last_week);
    # this._fillInComparePercent(targetSel+" .compare-last-same-period", lastSamePeriodUsage, averageUsage, this.multiLangTexts.samePeriodLastYear);
    beginning_usage = sum([ g['beginningWeekdayInfo']['average'] for g in group_data])
    average_usage = sum([ g['currentWeekdayInfo']['average'] for g in group_data])

    last_weekday_usage = sum([ g['lastWeekdayInfo']['average'] for g in group_data])
    current_weekday_usage = sum([ g['currentWeekdayInfo']['average'] for g in group_data])

    weekday_compare_last = None
    if last_weekday_usage > 0:
        weekday_compare_last = float(current_weekday_usage - last_weekday_usage)/last_weekday_usage*100
    m['weekday_month_compare_helper'] = CompareTplHepler(weekday_compare_last)

    last_same_period = sum([ g['lastSamePeriodWeekdayInfo']['average'] for g in group_data])

    weekday_compare_same_period = None
    if last_same_period > 0 :
        weekday_compare_same_period = float(average_usage - last_same_period)/last_same_period*100

    m['weekday_compare_same_period'] = weekday_compare_same_period
    m['weekday_same_period_compare_helper'] = CompareTplHepler(weekday_compare_same_period)

    for ix, g in enumerate(group_data):
        g['color'] = type_colors[ix % len(type_colors)]
        g['system'] = System.objects.get(code=g['systemCode'])

        if len(g['sourceIds']) == 1:
            g['title'] = get_source_name(g['sourceIds'][0])
        else:
            g['title'] = g['system'].name

        g['usage'] = g['currentWeekdayInfo']['average']
        beginning_usage = g['beginningWeekdayInfo']['average']
        average_usage = g['currentWeekdayInfo']['average']

        unit_infos = json.loads(g['system'].unit_info)
        money_unit_code = unit_infos['money']
        money_unit_rate = UnitRate.objects.filter(category_code='money', code=unit_infos['money']).first()

        weekday_costs = [get_weekdays_cost_by_source_readings(current_system, sid, report_date, report_end_date) for sid in g['sourceIds']]
        g['usage_bill'] = sum([c for c in weekday_costs if c is not None])

        compare_last_month = None
        if beginning_usage > 0:
            compare_last_month = float(average_usage - beginning_usage)/beginning_usage*100

        g['compare_last_month'] = compare_last_month


        # for weekday
        weekday = {}

        last_weekday_usage = g['lastWeekdayInfo']['average']
        current_weekday_usage = g['currentWeekdayInfo']['average']

        weekday_compare_last = None
        if last_weekday_usage > 0:
            weekday_compare_last = float(current_weekday_usage - last_weekday_usage)/last_weekday_usage*100

        weekday['compare_last_helper'] = CompareTplHepler(weekday_compare_last)
        g['weekday'] = weekday


        compare_same_period = None
        last_same_period = g['lastSamePeriodWeekdayInfo']['average']
        if last_same_period > 0:
            compare_same_period = float(average_usage - last_same_period)/last_same_period*100

        g['compare_same_period'] = compare_same_period

        weekend = {'bill': g['currentWeekendInfo']['average'] * money_unit_rate.rate}
        weekend_beginning_usage = g['beginningWeekendInfo']['average']
        weekend_average_usage = g['currentWeekendInfo']['average']

        weekend_last_usage = g['lastWeekendInfo']['average']
        weekend_current_usage = g['currentWeekendInfo']['average']

        weekend_compare_last = None
        if weekend_last_usage > 0:
            weekend_compare_last = float(weekend_current_usage - weekend_last_usage)/weekend_last_usage*100

        weekend['compare_last_helper'] = CompareTplHepler(weekend_compare_last)

        weekend_compare_same = None
        weekend_last_same_period_avg = g['lastSamePeriodWeekendInfo']['average']
        if weekend_last_same_period_avg > 0:
            weekend_compare_same = float(weekend_average_usage - weekend_last_same_period_avg)/weekend_last_same_period_avg*100

        weekend['compare_same_period_helper'] = CompareTplHepler(weekend_compare_same)

        g['weekend'] = weekend


        # for overnight
        overnight = {'bill': get_overnight_avg_cost(current_system, g['sourceIds'], report_date, report_end_date)}

        last_overnight_usage = g['lastOvernightInfo']['average']
        current_overnight_usage = g['currentOvernightInfo']['average']

        overnight_compare_last = None
        if last_overnight_usage > 0:
            overnight_compare_last = float(current_overnight_usage - last_overnight_usage)/last_overnight_usage*100

        overnight['compare_last_helper'] = CompareTplHepler(overnight_compare_last)

        overnight_compare_same = None
        overnight_average_usage = g['currentOvernightInfo']['average']
        overnight_last_same_period_avg = g['lastSamePeriodOvernightInfo']['average']
        if overnight_last_same_period_avg > 0:
            overnight_compare_same = float(overnight_average_usage - overnight_last_same_period_avg)/overnight_last_same_period_avg*100

        overnight['compare_same_period_helper'] = CompareTplHepler(overnight_compare_same)


        g['overnight'] = overnight


    if current_lang()=="zh-tw":
        compare_current_name = DateFormat(report_date).format("n")+_("tcmonth")
        compare_last_name = DateFormat(report_date - relativedelta(months=1)).format("n")+_("tcmonth")
    else:
        compare_current_name = DateFormat(report_date).format("M")
        compare_last_name = DateFormat(report_date - relativedelta(months=1)).format("M")
    if report_type == 'week':
        compare_current_name = _('This week')
        compare_last_name = _('Last week')
    elif report_type == 'quarter':
        compare_current_name = _('This quarter')
        compare_last_name = _('Last quarter')
    elif report_type == 'year':
        compare_current_name = report_date.strftime('%Y')
        compare_last_name = (report_date-relativedelta(years=1)).strftime('%Y')
    elif report_type == 'custom':
        compare_current_name = _('This period')
        compare_last_name = _('Last same period')



    m['compare_current_name'] = compare_current_name
    m['compare_last_name'] = compare_last_name

    # sub compare graphs
    sub_compare_graphs = []

    combined_weekday_readings_g = {}
    # this is combined current readings
    combined_readings = {}
    combined_readings_g = {}

    combined_overnight_readings = {}
    combined_overnight_readings_g = {}


    # for weekday
    # combined_current_readings = {};
    combined_last_readings = {};
    for ix, g in enumerate(group_data):
        current_readings = g['currentReadings']
        overnight_readings = g['overnightcurrentReadings']
        g['compare_last_month_helper'] = CompareTplHepler(g['compare_last_month'])
        g['compare_same_period_helper'] = CompareTplHepler(g['compare_same_period'])

        for ts, val in current_readings.items():
            if ts in combined_readings:
                combined_readings[ts] += val
                combined_readings_g[ts].append((g,val-g['currentWeekendInfo']['average']))
                combined_weekday_readings_g[ts].append((g,val-g['currentWeekdayInfo']['average']))
            else:
                combined_readings[ts] = val
                combined_readings_g[ts] = [(g,val-g['currentWeekendInfo']['average'])]
                combined_weekday_readings_g[ts] = [(g,val-g['currentWeekdayInfo']['average'])]

        for ts, val in overnight_readings.items():
            if ts in combined_overnight_readings:
                combined_overnight_readings[ts] += val
                combined_overnight_readings_g[ts].append((g,val-g['currentOvernightInfo']['average']))
            else:
                combined_overnight_readings[ts] = val
                combined_overnight_readings_g[ts] = [(g,val-g['currentOvernightInfo']['average'])]

        last_readings = g['lastReadings']
        for ts, val in last_readings.items():
            if ts in combined_last_readings:
                combined_last_readings[ts] += val
            else:
                combined_last_readings[ts] = val

        last_total = sum(last_readings.values())
        current_total = sum(current_readings.values())

        total_compare = None
        if last_total:
            total_compare = float(current_total- last_total)/last_total*100

        chart_title = 'N/A'
        if total_compare:
            if(CompareTplHepler(total_compare).compared_percent >=0):
                chart_title = _('Overall: {0.compared_percent_abs:.0f}&#37; more energy than last {1}').format(CompareTplHepler(total_compare), report_type_name)
            else:
                chart_title = _('Overall: {0.compared_percent_abs:.0f}&#37; less energy than last {1}').format(CompareTplHepler(total_compare), report_type_name)
        current_day_readings = {}
        # for day in range(1, 32):
        #     current_day_readings[day] = None

        for ts, v in current_readings.items():
            dt = datetime.datetime.fromtimestamp(ts, pytz.utc)
            dt = dt.astimezone(current_system_tz)
            current_day_readings[dt] = v

        last_day_readings = {}
        # for day in range(1, 32):
        #     last_day_readings[day] = None

        for ts, v in last_readings.items():
            dt = datetime.datetime.fromtimestamp(ts, pytz.utc)
            dt = dt.astimezone(current_system_tz)
            last_day_readings[dt] = v

        graph_title = get_source_name(g['sourceIds'][0]) if g['system'].code == m['company_system'].code else g['system'].name
        # [{'name': 'last', 'value': v, 'datetime': datetime.datetime.fromtimestamp(t, pytz.utc) } for t, v in combined_last_readings.items()]
        sub_graph = {
            'system': g['system'],
            'color': type_colors[ix % len(type_colors)],
            'title': graph_title,
            'current_reading_serie': json.dumps([{'name': compare_current_name, 'value': v, 'datetime': t} for t, v in current_day_readings.items()], cls=DjangoJSONEncoder),
            'last_reading_serie': json.dumps([{'name': compare_last_name, 'value': v, 'datetime': t} for t, v in last_day_readings.items()], cls=DjangoJSONEncoder),
            'chart_title': chart_title
        }
        sub_compare_graphs.append(sub_graph)

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

    # m['compare_current_readings_series']= json.dumps(combined_readings.values(), cls=DjangoJSONEncoder)

    current_series = [{'name': compare_current_name, 'type': 'current', 'value': v, 'datetime': datetime.datetime.fromtimestamp(t, pytz.utc).astimezone(current_system_tz)} for t, v in combined_readings.items()]

    m['compare_current_readings_series']= json.dumps(current_series, cls=DjangoJSONEncoder)

    last_series = [{'name': compare_last_name, 'type': 'last', 'value': v, 'datetime': datetime.datetime.fromtimestamp(t, pytz.utc).astimezone(current_system_tz) } for t, v in combined_last_readings.items()]

    compare_series = current_series + last_series

    # m['compare_last_readings_series']= json.dumps(combined_last_readings.values(), cls=DjangoJSONEncoder)
    m['compare_series']= json.dumps(compare_series, cls=DjangoJSONEncoder)


    # m['compare_last_categories'] = json.dumps(map(str, range(1, 32)))
    m['compare_last_categories'] = json.dumps(range(1, 32))
    m['compare_last_label_step'] = 2

    if report_type == 'year':
        m['compare_last_categories'] = range(366)
        m['compare_last_label_step'] = 29

    m['sub_compare_graphs'] = sub_compare_graphs


    highest_datetime, highest_usage= sorted(combined_readings.items(), key=lambda x: x[1])[-1]

    def weekday_filter(tv):
        t, v = tv
        wd = datetime.datetime.fromtimestamp(t, pytz.utc).weekday()
        return wd >= 0 and wd <=4

    only_weekday_readings = filter(weekday_filter, combined_readings.items())

    wd_highest_usage = None
    wd_highest_datetime = None

    if only_weekday_readings:
        wd_highest_datetime, wd_highest_usage= sorted(only_weekday_readings, key=lambda x: x[1])[-1]

    # m['highest_value']

    m['weekday_highest_usage'] = highest_usage
    m['weekday_highest_datetime'] = datetime.datetime.fromtimestamp(highest_datetime, pytz.utc)

    if wd_highest_datetime:
        wd_highest_datetime = datetime.datetime.fromtimestamp(wd_highest_datetime, pytz.utc)
        m['weekday_highest_usage'] = wd_highest_usage * get_unitrate_by_system(current_system, wd_highest_datetime).rate

    m['weekday_highest_datetime'] = wd_highest_datetime

    m['weekday_details'] = group_data
    m['saving_info'] = report_data['savingInfo']

    def weekend_filter(tv):
        t, v = tv
        dt = datetime.datetime.fromtimestamp(t, pytz.utc).astimezone(current_system_tz)
        wd = dt.weekday()
        all_holidays = system.get_all_holidays()
        return (wd >= 5 and wd <=6) or dt.date() in all_holidays

    only_weekend_readings = filter(weekend_filter, combined_readings.items())

    we_highest_usage = None
    we_highest_datetime = None

    if only_weekend_readings:
        we_highest_datetime, we_highest_usage= sorted(only_weekend_readings, key=lambda x: x[1])[-1]


    if we_highest_datetime:
        m['weekend_highest_g'], _v = sorted(combined_readings_g[we_highest_datetime], key=lambda x: x[1])[-1]
        we_highest_datetime = datetime.datetime.fromtimestamp(we_highest_datetime, pytz.utc)

        m['weekend_highest_usage'] = we_highest_usage*get_unitrate_by_system(current_system, we_highest_datetime).rate
    m['weekend_highest_datetime'] = we_highest_datetime


    if highest_datetime:
        m['highest_diff_source'], _v = sorted(combined_weekday_readings_g[highest_datetime], key=lambda x: x[1])[-1]


    only_overnight_readings = combined_overnight_readings.items()

    overnight_highest_usage = None
    overnight_highest_datetime = None

    if only_overnight_readings:
        overnight_highest_datetime, overnight_highest_usage= sorted(only_overnight_readings, key=lambda x: x[1])[-1]

    if overnight_highest_datetime:
        m['overnight_highest_g'], _v = sorted(combined_overnight_readings_g[overnight_highest_datetime], key=lambda x: x[1])[-1]
        overnight_highest_datetime = datetime.datetime.fromtimestamp(overnight_highest_datetime, pytz.utc)

        m['overnight_highest_usage'] = overnight_highest_usage * get_unitrate_by_system(current_system, overnight_highest_datetime).rate
    m['overnight_highest_datetime'] = overnight_highest_datetime

    # oops!!! have to rewrite
    p_or_n = -1 if report_data['savingInfo']['energy'] >=0 else 0

    m['saving_energy'] = abs(report_data['savingInfo']['energy'])
    m['css_class_energy_saving'] = 'positive-saving' if report_data['savingInfo']['energy'] >=0 else 'negative-saving'
    m['is_saving'] = (report_data['savingInfo']['energy'] >=0)
    # in tons
    m['saving_co2'] = abs(report_data['savingInfo']['co2'] / 1000.0)
    m['saving_money'] = abs(report_data['savingInfo']['money'])

    m['co2_in_car'] = abs(report_data['savingInfo']['co2']*0.003)
    m['co2_in_forest'] = abs(report_data['savingInfo']['co2']*0.016)
    m['co2_in_elephant'] = abs(report_data['savingInfo']['kwh']*0.0417)
    # var co2InCar = Utils.formatWithCommas(Math.abs((reportGenThis.savingInfo.co2*0.003).toFixed(0)));

    # lastSamePeriodUsage += info[lastSamePeriodUsageKey].average;

    # this.generateCalendarReport('#weekday-info', combinedReadings,
    #     'currentWeekdayInfo', 'beginningWeekdayInfo',
    #     'lastWeekdayInfo', 'lastSamePeriodWeekdayInfo', lowestUsage, lowestDt, highestUsage, highestDt,
    #     false, isNotConcernFunc, 'weekday-sub-calendar', this.multiLangTexts.calendarTypeWeekday,
    #     this.multiLangTexts.calendarSplitWeekdays, this.multiLangTexts.calendarSplitWeekends);

    transformed_datas = []
    energy_percentsum = 0
    energy_max_value = 0

    for ix, g in enumerate(group_data):
        if g['currentTotalEnergy'] > energy_max_value:
            energy_max_value = g['currentTotalEnergy']

    transformed_total_energy = sum([ g['currentTotalEnergy'] for g in group_data])
    for ix, g in enumerate(group_data):
        change_in_kwh = None
        if 'last_year_this_month' in g and g['last_year_this_month']['money'] > 0:
            change_in_kwh = (g['currentTotalMoney'] - g['last_year_this_month']['money'])/g['last_year_this_month']['money'] * 100

        percent_in_total = float(g['currentTotalEnergy']/transformed_total_energy) * 100

        percent_base_on_max = 0
        if energy_max_value > 0:
            percent_base_on_max = float(g['currentTotalEnergy']/energy_max_value) * 100

        change_in_money = None
        if 'last_year_this_month' in g and g['last_year_this_month']['money']:
            change_in_money = g['currentTotalMoney']- g['last_year_this_month']['money']

        data_info = {
            'total_energy': g['currentTotalEnergy'],
            'co2_val': g['currentTotalCo2'],
            'money_val': g['currentTotalMoney'],
            'change_in_kwh': change_in_kwh,
            'change_in_money': change_in_money,
            'percent_in_total': percent_in_total,
            'percent_base_on_max': percent_base_on_max,
            'color': type_colors[ix % len(type_colors)]
        }
        data_info['name'] = g['sourceNameInfo'][current_lang()] if g['systemCode'] == m['company_system'].code else g['system'].name
        transformed_datas.append(data_info)

    m['transformed_datas'] = transformed_datas


    transformed_bars = [{'name': td['name'], 'data': [td['total_energy']], 'color': type_colors[i % len(type_colors)]} for i, td in enumerate(transformed_datas)]

    m['transformed_bars_json'] = json.dumps(transformed_bars)

    transformed_pie = [{'category': td['name'], 'value': td['total_energy'], 'color': type_colors[i % len(type_colors)]} for i, td in enumerate(transformed_datas)]

    m['transformed_pie_json'] = json.dumps(transformed_pie)

    compare_last_month_helper = CompareTplHepler(compare_to_last_month)
    m['barchart_compare_text'] = _("Your energy consumption this {1} was {0} than it was last {1}").format(
        compare_last_month_helper.formated_percent_change,
        report_type_name
    )

    m['barchart_title'] = _('Total energy consumption for the last 6 months (kWh)')

    if report_type == 'week':
        m['barchart_title'] = _('Total energy consumption for the last 6 weeks (kWh)')
    elif report_type == 'quarter':
        m['barchart_title'] = _('Total energy consumption for the last 6 quarters (kWh)')
    elif report_type == 'year':
        m['barchart_title'] = _('Total energy consumption for the last 6 years (kWh)')
    elif report_type == 'custom':
        m['barchart_title'] = _('Total energy consumption for the last 6 same periods (kWh)')

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


    compare_past_date = report_date
    compare_past_date_end = report_end_date

    compare_past_datasource = []
    for su in sumup_usages:
        if report_type == 'month':
            formated_date = formats.date_format(compare_past_date, 'SHORT_MONTH_FORMAT')
        elif report_type == 'week':
            formated_date = u'{0} - {1}'.format(
                formats.date_format(compare_past_date, 'MONTH_DAY_FORMAT'),
                formats.date_format(compare_past_date_end, 'MONTH_DAY_FORMAT'))
        elif report_type == 'quarter':
            formated_date = '{0} Q{1}'.format(compare_past_date.strftime("%Y"), compare_past_date.month/3 + 1)
        elif report_type == 'year':
            formated_date = formats.date_format(compare_past_date, 'YEAR_FORMAT')
        elif report_type == 'custom':
            formated_date = u'{0} - {1}'.format(
                formats.date_format(compare_past_date, 'MONTH_DAY_FORMAT'),
                formats.date_format(compare_past_date_end, 'MONTH_DAY_FORMAT'))

        compare_past_datasource.append({
            'value': su,
            'month': compare_past_date.strftime('%b'),
            'datetime': compare_past_date,
            'formated_date': formated_date,
            'country': "us"})
        if report_type == 'month':
            compare_past_date = compare_past_date - relativedelta(months=1)
            compare_past_date_end -= relativedelta(months=1)
        elif report_type == 'week':
            compare_past_date = compare_past_date - relativedelta(days=7)
            compare_past_date_end -= relativedelta(days=7)
        elif report_type == 'quarter':
            compare_past_date = compare_past_date - relativedelta(months=3)
            compare_past_date_end -= relativedelta(months=3)
        elif report_type == 'year':
            compare_past_date = compare_past_date - relativedelta(years=1)
            compare_past_date_end -= relativedelta(years=1)
        elif report_type == 'custom':
            compare_past_date = compare_past_date - relativedelta(days=m['report_day_diff'])
            compare_past_date_end -= relativedelta(days=m['report_day_diff'])

    compare_past_datasource.reverse()

    # oops, hack?
    m['compare_past_datasource_json'] = json.dumps(compare_past_datasource, cls=DjangoJSONEncoder)

    # weekends
    weekends_usage = {}
    weekends_usage['total_bill'] = sum([ g['currentWeekendInfo']['average'] for g in group_data]) * money_unit_rate.rate;

    # beginningWeekendInfo
    weekends_beginning_usage = sum([ g['beginningWeekendInfo']['average'] for g in group_data])
    weekends_average_usage = sum([ g['currentWeekendInfo']['average'] for g in group_data])

    weekends_last_usage = sum([ g['lastWeekendInfo']['average'] for g in group_data])
    weekends_current_usage = sum([ g['currentWeekendInfo']['average'] for g in group_data])

    # average_usage = sum([ g['currentWeekdayInfo']['average'] for g in group_data])
    weekends_compare_last = None
    if weekends_last_usage > 0:
        weekends_compare_last = float(weekends_current_usage - weekends_last_usage)/weekends_last_usage*100

    weekends_usage['month_compare_helper'] = CompareTplHepler(weekends_compare_last)

    weekends_last_same_period = sum([ g['lastSamePeriodWeekendInfo']['average'] for g in group_data])
    weekends_compare_same_period = None
    if weekends_last_same_period > 0 :
        weekends_compare_same_period = float(weekends_average_usage - weekends_last_same_period)/weekends_last_same_period*100

    weekends_usage['same_period_compare_helper'] = CompareTplHepler(weekends_compare_same_period)


    m['weekends'] = weekends_usage

    # overnight
    overnight_usage = {}
    overnight_bill = sum([ g['currentOvernightInfo']['average'] for g in group_data])
    # overnight_usage['bill'] = overnight_bill * money_unit_rate.rate
    overnight_usage['bill'] = get_overnight_avg_cost(current_system, source_ids, report_date, report_end_date)

    overnight_beginning_usage = sum([ g['beginningOvernightInfo']['average'] for g in group_data])
    overnight_average_usage = sum([ g['currentOvernightInfo']['average'] for g in group_data])

    overnight_last_usage = sum([ g['lastOvernightInfo']['average'] for g in group_data])
    overnight_current_usage = sum([ g['currentOvernightInfo']['average'] for g in group_data])

    # average_usage = sum([ g['currentWeekdayInfo']['average'] for g in group_data])
    overnight_compare_last = None
    if overnight_last_usage > 0:
        overnight_compare_last = float(overnight_current_usage - overnight_last_usage)/overnight_last_usage*100

    overnight_usage['compare_last_helper'] = CompareTplHepler(overnight_compare_last)

    overnight_last_same_period = sum([ g['lastSamePeriodOvernightInfo']['average'] for g in group_data])
    overnight_compare_same_period = None
    if overnight_last_same_period > 0 :
        overnight_compare_same_period = float(overnight_average_usage - overnight_last_same_period)/overnight_last_same_period*100

    overnight_usage['compare_same_period_helper'] = CompareTplHepler(overnight_compare_same_period)

    m['overnight'] = overnight_usage

    if current_system.night_time_start.minute > 29:
        tmpDateStart = datetime.datetime.combine(datetime.date.today(), current_system.night_time_start) + datetime.timedelta(hours=1)    
        tmpDateStart = tmpDateStart.time()
    else:
        tmpDateStart = current_system.night_time_start

    if current_system.night_time_end.minute > 29:
        tmpDateEnd = datetime.datetime.combine(datetime.date.today(), current_system.night_time_end) + datetime.timedelta(hours=1)
        tmpDateEnd = tmpDateEnd.time()
    else:
        tmpDateEnd = current_system.night_time_end

    m['overnight_timerange_text'] = "{0} - {1}".format(
        tmpDateStart.strftime('%l%p').strip(),
        tmpDateEnd.strftime('%l%p').strip())

    # holidays
    m['holidays_json'] = json.dumps(report_data['holidays'])


    if to_pdf:
        return PDFTemplateResponse(
            request=request,
            template='companies/reports/report.html',
            filename='report.pdf',
            context=m,
            # show_content_in_browser=False,
            cmd_options={
                'page-size': 'A3',
                'javascript-delay': 1000,
                # 'quiet': '',
                # 'margin-left': '18mm',
                # 'page-size': 'A3',
                # 'margin-top': 50,
                # 'quiet': '',
                # 'load-media-error-handling': 'ignore',
                # 'load-error-handling': 'ignore'
            },
        )


    return render(request, 'companies/reports/popup_report.html', m)


@permission_required()
def popup_report_view(request, system_code, year=None, month=None, report_type=None, to_pdf=False):
    return _popup_report_view(request, system_code)

@permission_required()
def download_popup_report_view(request, system_code):
    return _popup_report_view(request, system_code, to_pdf=True)


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
