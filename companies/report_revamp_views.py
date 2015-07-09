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

from entrak.auth.decorators import require_passes_test


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
        datetime__lt=end_dt)

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

    # return system.overnight_avg_cost(start_dt, end_dt, source_ids)

    date_ranges = []

    unit_infos = json.loads(system.unit_info)
    # money_unit_code = unit_infos['money']
    # money_unit_rate = UnitRate.objects.filter(category_code='money', code=unit_infos['money']).first()
    money_unit_rates = UnitRate.objects.filter(category_code='money', code=unit_infos['money']).order_by('effective_date')
    system_tz = system.time_zone

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
        num_day = (ed.date() - sd.date()).days
        rdays = [sd+datetime.timedelta(days=n) for n in range(num_day)]
        for rday in rdays:
            on_sd = rday.astimezone(system_tz).replace(hour=system.night_time_start.hour)
            on_ed = rday.astimezone(system_tz).replace(hour=system.night_time_end.hour) + relativedelta(days=1)

            q = MQ(datetime__gte=on_sd, datetime__lt=on_ed)
            mqs.append(q)

        conds = reduce(
            operator.or_,
            mqs
        )

        dr_sum = r.rate * SourceReadingHour.objects(conds, source_id__in=source_ids).sum('value')
        total_on_sum += dr_sum

    # dirty way to count number of days
    total_day = (end_dt.date() - start_dt.date()).days + 1
    today = datetime.datetime.now(pytz.utc).astimezone(system_tz)
    if end_dt > today:
        total_day = (today.date() - start_dt.date()).days + 1

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
        start_dt = dateparse.parse_date(sd)
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
        last_start_dt = start_dt - relativedelta(months=1)
        last_end_dt = end_dt - relativedelta(months=1)

    total_cost = current_system.total_usage(start_dt, end_dt)['totalMoney']
    last_total_cost = current_system.total_usage(last_start_dt, last_end_dt)['totalMoney']

    compare_to_last_total = None

    if last_total_cost > 0 and total_cost > 0:
        compare_to_last_total = float(total_cost-last_total_cost)/last_total_cost*100

    weekday_usage = current_system.total_weekday_weekend_usage(start_dt, end_dt, "weekday")

    if len(weekday_usage['dates']) > 0:
        weekday_cost = weekday_usage['totalMoney'] / len(weekday_usage['dates'])
    else:
        weekday_cost = 0

    compare_to_last_weekday = None

    last_weekday_usage = current_system.total_weekday_weekend_usage(last_start_dt, last_end_dt, "weekday")

    if len(last_weekday_usage['dates']) > 0:
        last_weekday_cost = last_weekday_usage['totalMoney'] / len(last_weekday_usage['dates'])
    else:
        last_weekday_cost = 0

    if last_weekday_cost > 0 and weekday_cost > 0:
        compare_to_last_weekday = float(weekday_cost-last_weekday_cost)/last_weekday_cost*100

    # m = systems_info
    m = {}

    m['formated_total_cost'] = '${0:,.0f}'.format(total_cost) if total_cost is not None else None
    m['formated_weekday_cost'] = '${0:,.0f}'.format(weekday_cost) if weekday_cost is not None else None

    m['compare_to_last_total'] = CompareTplHepler(compare_to_last_total).to_dict()
    m['compare_to_last_weekday'] = CompareTplHepler(compare_to_last_weekday).to_dict()

    overnight_usage = current_system.overnight_usage(start_dt, end_dt, source_ids)

    if len(overnight_usage['dates']) > 0:
        overnight_avg_cost = overnight_usage['totalMoney'] / len(overnight_usage['dates'])
    else:
        overnight_avg_cost = 0

    m['formated_overnight_avg_cost'] = '${0:,.0f}'.format(overnight_avg_cost) if overnight_avg_cost else None

    compare_to_last_overnight_avg_cost = None

    last_overnight_usage = current_system.overnight_usage(last_start_dt, last_end_dt, source_ids)

    if len(last_overnight_usage['dates']) > 0:
        last_overnight_avg_cost = last_overnight_usage['totalMoney'] / len(last_overnight_usage['dates'])
    else:
        last_overnight_avg_cost = 0

    if last_overnight_avg_cost > 0 and overnight_avg_cost > 0:
        compare_to_last_overnight_avg_cost = float(overnight_avg_cost-last_overnight_avg_cost)/last_overnight_avg_cost*100

    m['compare_to_last_overnight_avg_cost'] = CompareTplHepler(compare_to_last_overnight_avg_cost).to_dict()

    return HttpResponse(json.dumps(m, cls=DjangoJSONEncoder), content_type="application/json")


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

    m = systems_info
    # m["monthly_summary"] = sorted(monthly_summary, key=lambda x: x['timestamp'], reverse=True)

    m['default_date'] = start_dt
    m['today_date'] = datetime.datetime.now(pytz.utc)
    m['default_custom_end_date'] = datetime.datetime.now(pytz.utc) - datetime.timedelta(days=1)
    m['default_custom_start_date'] = m['default_custom_end_date'] - datetime.timedelta(days=30)
    # return render(request, 'testing_code.html', m)
    return render(request, 'companies/reports/summary_revamp.html', m)


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


def _popup_report_view(request, system_code, year=None, month=None, report_type=None, to_pdf=False, share=False):
    # systems_info = System.get_systems_info(system_code, request.user.system.code)
    systems_info = System.get_systems_info(system_code, system_code) # in fact just using systems no user systems
    systems = systems_info['systems']

    current_system = System.objects.get(code=system_code)

    sources = current_system.sources
    source_ids = [str(source.id) for source in sources]

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
    # source_readings = SourceManager.get_readings_with_target_class(source_ids, SourceReadingMonth, start_dt, end_dt)

    m = {}
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
        report_date = current_system_tz.localize(datetime.datetime.strptime(sd + ' 00:00:00', '%Y-%m-%d %H:%M:%S'))

    end_dt = start_dt + relativedelta(months=1)

    ed = request.GET.get('end_date')
    if ed:
        report_end_date = current_system_tz.localize(datetime.datetime.strptime(ed + ' 00:00:00', '%Y-%m-%d %H:%M:%S'))

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

    if report_type == 'month':
        last_start_dt = report_date - relativedelta(months=1)
        last_end_dt = report_end_date - relativedelta(months=1)
    elif report_type == 'week':
        last_start_dt = report_date - datetime.timedelta(days=7)
        last_end_dt = report_end_date - datetime.timedelta(days=7)
    elif report_type == 'quarter':
        last_start_dt = report_date - relativedelta(months=3)
        last_end_dt = report_end_date - relativedelta(months=3)
    elif report_type == 'year':
        last_start_dt = report_date - relativedelta(years=1)
        last_end_dt = report_end_date - relativedelta(years=1)
    elif report_type == 'custom':
        last_start_dt = report_date - relativedelta(months=1)
        last_end_dt = report_end_date - relativedelta(months=1)

    m['sub_systems'] = current_system.direct_sources_and_systems(current_lang())

    def generate_section_1_summary(system, start_date, end_date, m):
        # beginning of section 1a summary stats
        current_usage = system.total_usage(start_date, end_date)
        last_year_usage = system.total_usage(start_date - relativedelta(years=1), end_date - relativedelta(years=1))

        m['s1_total_money'] = current_usage['totalMoney']
        m['s1_total_kwh'] = current_usage['totalKwh']
        m['s1_total_co2'] = current_usage['totalCo2']/1000

        if last_year_usage['totalKwh'] > 0:

            m['s1_last_year_data_exist'] = True

            m['s1_diff_kwh'] = abs(current_usage['totalKwh'] - last_year_usage['totalKwh'])*100/last_year_usage['totalKwh']
            diff_co2 = abs(current_usage['totalCo2'] - last_year_usage['totalCo2'])
            m['s1_diff_money'] = abs(current_usage['totalMoney'] - last_year_usage['totalMoney'])
            m['s1_co2_in_car'] = diff_co2*0.003
            m['s1_co2_in_forest'] = diff_co2*0.016
            m['s1_kwh_in_aircons'] = abs(current_usage['totalKwh'] - last_year_usage['totalKwh'])*0.0417
            m['s1_diff_co2'] = diff_co2/1000

            if current_usage['totalKwh'] <= last_year_usage['totalKwh']:
                m['s1_is_saving'] = True
                m['s1_css_class_energy_saving'] = 'positive-saving'
            else:
                m['s1_is_saving'] = False
                m['s1_css_class_energy_saving'] = 'negative-saving'
        else:
            m['s1_last_year_data_exist'] = False
        # end of section 1a summary stats

        # start of section 1b sub-systems bar chart and table

        sub_system_stats = []
        sub_system_jsons = []
        sources = system.sources
        source_ids = [s.id for s in sources]
        max_kwh = 0
        total_kwh = 0

        sources_current_usage = system.total_usage_by_source_id(start_date, end_date, source_ids)
        sources_last_year_usage = system.total_usage_by_source_id(start_date - relativedelta(years=1), end_date - relativedelta(years=1), source_ids)

        for ix, sub_system in enumerate(m['sub_systems']):

            current_kwh = 0
            current_co2 = 0
            current_money = 0
            last_year_kwh = 0
            last_year_money = 0
            change_in_kwh = None
            change_in_money = None

            sys = sub_system["object"]

            if isinstance(sys, System):
                child_sources = sys.sources

                for src in child_sources:
                    if src.id in sources_current_usage:
                        current_kwh += sources_current_usage[src.id]['totalKwh']
                        current_co2 += sources_current_usage[src.id]['totalCo2']
                        current_money += sources_current_usage[src.id]['totalMoney']
                    if src.id in sources_last_year_usage:
                        last_year_kwh += sources_last_year_usage[src.id]['totalKwh']
                        last_year_money += sources_last_year_usage[src.id]['totalMoney']

            else:
                if sys.id in sources_current_usage and sources_current_usage[sys.id]['totalKwh'] > 0:
                    current_kwh = sources_current_usage[sys.id]['totalKwh']
                    current_co2 = sources_current_usage[sys.id]['totalCo2']
                    current_money = sources_current_usage[sys.id]['totalMoney']

                if sys.id in sources_last_year_usage and sources_last_year_usage[sys.id]['totalKwh'] > 0:
                    last_year_kwh = sources_last_year_usage[sys.id]['totalKwh']
                    last_year_money = sources_last_year_usage[sys.id]['totalMoney']

            if last_year_kwh > 0:
                change_in_kwh = (current_kwh - last_year_kwh)*100/last_year_kwh
                change_in_money = current_money - last_year_money

            if max_kwh < current_kwh:
                max_kwh = current_kwh

            if current_kwh == 0:
                current_kwh = None
                current_co2 = None
                current_money = None

            sub_system_stat = {
                'name': sub_system['name'],
                'total_kwh': current_kwh,
                'total_co2': current_co2,
                'total_money': current_money,
                'diff_kwh': change_in_kwh,
                'diff_money': change_in_money,
                'percent_base_on_max': None,
                'color': type_colors[ix % len(type_colors)],
            }

            sub_system_json = {
                'category': sub_system['name'],
                'color': type_colors[ix % len(type_colors)],
                'value': current_kwh,
            }

            sub_system_stats.append(sub_system_stat)
            sub_system_jsons.append(sub_system_json)

        for s in sub_system_stats:
            if max_kwh > 0:
                s['percent_base_on_max'] = s['total_kwh']*100/max_kwh


        m['s1_sub_system_stats'] = sub_system_stats
        m['s1_sub_system_json'] = json.dumps(sub_system_jsons)
        # assert False
        return m
        # end of section 1b sub-systems bar chart and table

    def generate_section_2_comparision(system, start_date, end_date, report_type, m):

        if report_type == 'month':
            interval = report_type.upper()
            interval_delta = relativedelta(months=1)
            report_start_dt = start_date - relativedelta(months=5)
            m['s2_barchart_title'] = _('Total energy consumption for the last 6 months (kWh)')
        elif report_type == 'week':
            interval = report_type.upper()
            interval_delta = relativedelta(days=7)
            report_start_dt = start_date - relativedelta(days=35)
            m['s2_barchart_title'] = _('Total energy consumption for the last 6 weeks (kWh)')
        elif report_type == 'quarter':
            interval = report_type.upper()
            interval_delta = relativedelta(months=3)
            report_start_dt = start_date - relativedelta(months=15)
            m['s2_barchart_title'] = _('Total energy consumption for the last 6 quarters (kWh)')
        elif report_type == 'year':
            interval = report_type.upper()
            interval_delta = relativedelta(years=1)
            report_start_dt = start_date - relativedelta(years=5)
            m['s2_barchart_title'] = _('Total energy consumption for the last 6 years (kWh)')
        elif report_type == 'custom':
            interval_delta = relativedelta(days=m['report_day_diff'])
            report_start_dt = start_date - relativedelta(days=5*m['report_day_diff'])
            m['s2_barchart_title'] = _('Total energy consumption for the last 6 same periods (kWh)')

        report_end_dt = end_date

        if report_type == 'custom':
            interval_usages = {}
            for x in range(6):
                period_end_date = report_end_dt - relativedelta(days=m['report_day_diff']*5)
                period_start_date = period_end_date - relativedelta(days=m['report_day_diff'])
                interval_usages[period_start_date.strftime('%Y%m%d')] = system.total_usage(period_start_date, period_end_date)
        else:
            interval_usages = system.total_usage_by_interval(report_start_dt, report_end_dt, interval)

        compare_datasource = []
        sub_system_compare_graphs = []
        interval_start_dt = report_start_dt
        interval_end_dt = end_date

        last_value = 0
        compare_value = 0

        for x in range(6):

            interval_start_dt = report_start_dt + interval_delta*x
            interval_end_dt = interval_start_dt + interval_delta - relativedelta(days=1)

            if report_type == 'month':
                interval_key = interval_start_dt.month
                formated_date = formats.date_format(interval_start_dt, 'SHORT_MONTH_FORMAT')
            elif report_type == 'week':
                interval_key = int(interval_start_dt.strftime('%U'))
                formated_date = u'{0} - {1}'.format(
                    formats.date_format(interval_start_dt, 'MONTH_DAY_FORMAT'),
                    formats.date_format(interval_end_dt, 'MONTH_DAY_FORMAT'),
                )
            elif report_type == 'quarter':
                interval_key = interval_start_dt.strftime('%Y%m')
                formated_date = '{0} Q{1}'.format(interval_start_dt.strftime("%Y"), interval_start_dt.month/3 + 1)
            elif report_type == 'year':
                interval_key = interval_start_dt.year
                formated_date = formats.date_format(interval_start_dt, 'YEAR_FORMAT')
            elif report_type == 'custom':
                interval_key = interval_start_dt.strftime('%Y%m%d')
                formated_date = u'{0} - {1}'.format(
                    formats.date_format(interval_start_dt, 'MONTH_DAY_FORMAT'),
                    formats.date_format(interval_end_dt, 'MONTH_DAY_FORMAT'),
                )

            if interval_key in interval_usages:
                value = interval_usages[interval_key]['totalKwh']
                if x == 5:
                    last_value = value
                if x == 4:
                    compare_value = value
            else:
                value = 0

            compare_datasource.append({
                'value': value,
                'month': interval_start_dt.strftime('%b'),
                'datetime': interval_start_dt,
                'formated_date': formated_date,
                'country': "us"})

        compare_datasource = sorted(compare_datasource, key=lambda k: k['datetime'])
        m['s2_compare_json'] = json.dumps(compare_datasource, cls=DjangoJSONEncoder)

        # assert False

        if compare_value > 0:
            compare_to_last_interval = (last_value - compare_value)*100/compare_value
        else:
            compare_to_last_interval = None

        compare_last_interval_helper = CompareTplHepler(compare_to_last_interval)
        m['s2_barchart_compare_text'] = _("Your energy consumption this {1} was {0} than it was last {1}").format(
            compare_last_interval_helper.formated_percent_change,
            report_type_name
        )

        if report_type == 'month':
            if current_lang()=="zh-tw":
                compare_current_name = DateFormat(start_date).format("n")+_("tcmonth")
                compare_last_name = DateFormat(start_date - interval_delta).format("n")+_("tcmonth")
            else:
                compare_current_name = DateFormat(start_date).format("M")
                compare_last_name = DateFormat(start_date - interval_delta).format("M")
        elif report_type == 'week':
            compare_current_name = _('This week')
            compare_last_name = _('Last week')
        elif report_type == 'quarter':
            compare_current_name = _('This quarter')
            compare_last_name = _('Last quarter')
        elif report_type == 'year':
            compare_current_name = start_date.strftime('%Y')
            compare_last_name = (start_date-relativedelta(years=1)).strftime('%Y')
        elif report_type == 'custom':
            compare_current_name = _('This period')
            compare_last_name = _('Last same period')

        m['s2_compare_current_name'] = compare_current_name
        m['s2_compare_last_name'] = compare_last_name

        current_daily_usage = system.total_usage_by_interval(start_date, end_date, "DAY")
        last_daily_usage = system.total_usage_by_interval(start_date - interval_delta, end_date - interval_delta, "DAY")

        def int_date_to_datetime(int_date, system_tz):
            return system_tz.localize(datetime.datetime.strptime('%d 00:00:00'%int_date, '%Y%m%d %H:%M:%S'))

        system_tz = system.time_zone
        current_series = [{'name': compare_current_name, 'type': 'current', 'value': v['totalKwh'], 'datetime': int_date_to_datetime(k, system_tz)} for k, v in current_daily_usage.items()]
        last_series = [{'name': compare_last_name, 'type': 'last', 'value': v['totalKwh'], 'datetime': int_date_to_datetime(k, system_tz)} for k, v in last_daily_usage.items()]
        compare_series = current_series + last_series

        m['s2_compare_series'] = json.dumps(compare_series, cls=DjangoJSONEncoder)

        for ix, sub_system in enumerate(m['sub_systems']):

            if isinstance(sub_system['object'], System):
                subsys_current_daily_usage = sub_system['object'].total_usage_by_interval(start_date, end_date, "DAY")
                subsys_last_daily_usage = sub_system['object'].total_usage_by_interval(start_date - interval_delta, end_date - interval_delta, "DAY")
            else:
                subsys_current_daily_usage = system.total_usage_by_interval(start_date, end_date, "DAY", [sub_system['id']])
                subsys_last_daily_usage = system.total_usage_by_interval(start_date - interval_delta, end_date - interval_delta, "DAY", [sub_system['id']])

            current_total = sum([v['totalKwh'] for k, v in subsys_current_daily_usage.items()])
            last_total = sum([v['totalKwh'] for k, v in subsys_last_daily_usage.items()])

            total_compare = None
            if last_total:
                total_compare = float(current_total- last_total)/last_total*100

            chart_title = 'N/A'
            if total_compare:
                if(CompareTplHepler(total_compare).compared_percent >=0):
                    chart_title = _('Overall: {0.compared_percent_abs:.0f}&#37; more energy than last {1}').format(CompareTplHepler(total_compare), report_type_name)
                else:
                    chart_title = _('Overall: {0.compared_percent_abs:.0f}&#37; less energy than last {1}').format(CompareTplHepler(total_compare), report_type_name)

            graph = {
                'color': type_colors[ix % len(type_colors)],
                'title': sub_system['name'],
                'current_series': json.dumps([{'name': compare_current_name, 'value': v['totalKwh'], 'datetime': int_date_to_datetime(k, system_tz)} for k, v in subsys_current_daily_usage.items()], cls=DjangoJSONEncoder),
                'last_series': json.dumps([{'name': compare_last_name, 'value': v['totalKwh'], 'datetime': int_date_to_datetime(k, system_tz)} for k, v in subsys_last_daily_usage.items()], cls=DjangoJSONEncoder),
                'chart_title': chart_title
            }
            sub_system_compare_graphs.append(graph)

        m['s2_sub_system_compare_graphs'] = sub_system_compare_graphs
        return m
        # end of section 2 comparision

    m = generate_section_1_summary(current_system, report_date, report_end_date + relativedelta(days=1), m)
    m = generate_section_2_comparision(current_system, report_date, report_end_date + relativedelta(days=1), report_type, m)

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

    m['weekday_bill'] = get_weekdays_cost(current_system, report_date, report_end_date + datetime.timedelta(days=1))


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

        weekend_last_year_usage = g['lastWeekendInfo']['average']
        weekend_current_usage = g['currentWeekendInfo']['average']

        weekend_compare_last = None
        if weekend_last_year_usage > 0:
            weekend_compare_last = float(weekend_current_usage - weekend_last_year_usage)/weekend_last_year_usage*100

        weekend['compare_last_helper'] = CompareTplHepler(weekend_compare_last)

        weekend_compare_same = None
        weekend_last_same_period_avg = g['lastSamePeriodWeekendInfo']['average']
        if weekend_last_same_period_avg > 0:
            weekend_compare_same = float(weekend_average_usage - weekend_last_same_period_avg)/weekend_last_same_period_avg*100

        weekend['compare_same_period_helper'] = CompareTplHepler(weekend_compare_same)

        g['weekend'] = weekend


        # for overnight
        last_overnight_usage = get_overnight_avg_cost(current_system, g['sourceIds'], report_date - relativedelta(months=1), report_end_date - relativedelta(months=1))
        current_overnight_usage = get_overnight_avg_cost(current_system, g['sourceIds'], report_date, report_end_date)

        overnight = {'bill': current_overnight_usage}

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

    # m['compare_last_categories'] = json.dumps(map(str, range(1, 32)))
    m['compare_last_categories'] = json.dumps(range(1, 32))
    m['compare_last_label_step'] = 2

    if report_type == 'year':
        m['compare_last_categories'] = range(366)
        m['compare_last_label_step'] = 29


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



    m['sum_up_usages'] = report_data['sumUpUsages']
    # max_sum_up = max(report_data['sumUpUsages'])
    sumup_usages = report_data['sumUpUsages']

    # weekends
    weekends_usage = {}
    weekends_usage['total_bill'] = sum([ g['currentWeekendInfo']['average'] for g in group_data]) * money_unit_rate.rate;

    # beginningWeekendInfo
    weekends_beginning_usage = sum([ g['beginningWeekendInfo']['average'] for g in group_data])
    weekends_average_usage = sum([ g['currentWeekendInfo']['average'] for g in group_data])

    weekends_last_year_usage = sum([ g['lastWeekendInfo']['average'] for g in group_data])
    weekends_current_usage = sum([ g['currentWeekendInfo']['average'] for g in group_data])

    # average_usage = sum([ g['currentWeekdayInfo']['average'] for g in group_data])
    weekends_compare_last = None
    if weekends_last_year_usage > 0:
        weekends_compare_last = float(weekends_current_usage - weekends_last_year_usage)/weekends_last_year_usage*100

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
    overnight_usage['bill'] = get_overnight_avg_cost(current_system, source_ids, report_date, report_end_date + datetime.timedelta(days=1))
    last_overnight_usage = get_overnight_avg_cost(current_system, source_ids, last_start_dt, last_end_dt + datetime.timedelta(days=1))

    overnight_beginning_usage = sum([ g['beginningOvernightInfo']['average'] for g in group_data])
    overnight_average_usage = sum([ g['currentOvernightInfo']['average'] for g in group_data])

    overnight_last_year_usage = sum([ g['lastOvernightInfo']['average'] for g in group_data])
    overnight_current_usage = sum([ g['currentOvernightInfo']['average'] for g in group_data])

    # average_usage = sum([ g['currentWeekdayInfo']['average'] for g in group_data])
    overnight_compare_last = None
    if last_overnight_usage > 0:
        overnight_compare_last = float(overnight_usage['bill'] - last_overnight_usage)/last_overnight_usage*100

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
            template='companies/reports/report_revamp.html',
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

    if share:
        return render(request, 'companies/reports/share_report_revamp.html', m)
    return render(request, 'companies/reports/popup_report_revamp.html', m)

# @permission_required()
def share_popup_report_view(request, system_code, year=None, month=None, report_type=None, to_pdf=False):
    return _popup_report_view(request, system_code, share=True)

from tokens.models import UrlToken
@require_passes_test(
    lambda r: UrlToken.objects.check_token_by_request(r) or r.user.is_authenticated())
def popup_report_view(request, system_code, year=None, month=None, report_type=None, to_pdf=False):
    return _popup_report_view(request, system_code)

# @permission_required()
@require_passes_test(
    lambda r: UrlToken.objects.check_token_by_request(r) or r.user.is_authenticated())
def download_popup_report_view(request, system_code):
    return _popup_report_view(request, system_code, to_pdf=True)

@require_passes_test(
    lambda r: UrlToken.objects.check_token_by_request(r) or r.user.is_authenticated())
def download_share_report_view(request, system_code):
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
