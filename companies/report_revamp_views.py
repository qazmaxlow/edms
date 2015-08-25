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

from baseline.models import BaselineUsage
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


def int_date_to_datetime(int_date, system_tz):
    return system_tz.localize(datetime.datetime.strptime('%d 00:00:00'%int_date, '%Y%m%d %H:%M:%S'))


def int_date_to_timestamp(int_date, system_tz):
    dt = system_tz.localize(datetime.datetime.strptime('%d 00:00:00'%int_date, '%Y%m%d %H:%M:%S'))
    return int(time.mktime(dt.astimezone(pytz.utc).timetuple()))


def get_source_name(source_id):
    source = Source.objects(id=str(source_id)).first()
    if (current_lang()=="zh-tw"):
        return source.d_name_tc
    return source.d_name


def generate_weekday_weekend_overnight_details(system, start_date, end_date, interval_delta, sub_systems, type_colors, gen_type='weekday'):

    if gen_type not in ['weekday', 'weekend', 'overnight']:
        gen_type = 'weekday'

    last_interval_start_date = start_date - interval_delta
    last_interval_end_date = end_date - interval_delta

    last_year_start_date = start_date - relativedelta(years=1)
    last_year_end_date = end_date - relativedelta(years=1)

    if gen_type in ['weekday', 'weekend']:
        source_current_usage = system.weekday_weekend_usage_by_source(start_date, end_date, gen_type)
        source_last_interval_usage = system.weekday_weekend_usage_by_source(last_interval_start_date, last_interval_end_date, gen_type)
        source_last_year_usage = system.weekday_weekend_usage_by_source(last_year_start_date, last_year_end_date, gen_type)
    else:
        source_current_usage = system.overnight_usage_by_source(start_date, end_date)
        source_last_interval_usage = system.overnight_usage_by_source(last_interval_start_date, last_interval_end_date)
        source_last_year_usage = system.overnight_usage_by_source(last_year_start_date, last_year_end_date)

    parent_current_cost = 0
    parent_current_kwh = 0
    parent_current_dates = set()
    parent_last_interval_cost = 0
    parent_last_interval_kwh = 0
    parent_last_interval_dates = set()
    parent_last_year_cost = 0
    parent_last_year_kwh = 0
    parent_last_year_dates = set()

    sub_system_stats = []

    for ix, sub_system in enumerate(sub_systems):

        current_cost = 0
        current_kwh = 0
        current_dates = set()
        last_interval_cost = 0
        last_interval_kwh = 0
        last_interval_dates = set()
        last_year_cost = 0
        last_year_kwh = 0
        last_year_dates = set()

        sys = sub_system["object"]

        if isinstance(sys, System):
            child_sources = sys.sources

            for src in child_sources:
                if src.id in source_current_usage:
                    current_cost += source_current_usage[src.id]['totalMoney']
                    current_kwh += source_current_usage[src.id]['totalKwh']
                    current_dates |= set(source_current_usage[src.id]['dates'])
                if src.id in source_last_interval_usage:
                    last_interval_cost += source_last_interval_usage[src.id]['totalMoney']
                    last_interval_kwh += source_last_interval_usage[src.id]['totalKwh']
                    last_interval_dates |= set(source_last_interval_usage[src.id]['dates'])
                if src.id in source_last_year_usage:
                    last_year_cost += source_last_year_usage[src.id]['totalMoney']
                    last_year_kwh += source_last_year_usage[src.id]['totalKwh']
                    last_year_dates |= set(source_last_year_usage[src.id]['dates'])

        else:
            if sys.id in source_current_usage:
                current_cost = source_current_usage[sys.id]['totalMoney']
                current_kwh = source_current_usage[sys.id]['totalKwh']
                current_dates = set(source_current_usage[sys.id]['dates'])
            if sys.id in source_last_interval_usage:
                last_interval_cost = source_last_interval_usage[sys.id]['totalMoney']
                last_interval_kwh = source_last_interval_usage[sys.id]['totalKwh']
                last_interval_dates = set(source_last_interval_usage[sys.id]['dates'])
            if sys.id in source_last_year_usage:
                last_year_cost = source_last_year_usage[sys.id]['totalMoney']
                last_year_kwh = source_last_year_usage[sys.id]['totalKwh']
                last_year_dates = set(source_last_year_usage[sys.id]['dates'])

        parent_current_cost += current_cost
        parent_current_kwh += current_kwh
        parent_current_dates |= current_dates
        parent_last_interval_cost += last_interval_cost
        parent_last_interval_kwh += last_interval_kwh
        parent_last_interval_dates |= last_interval_dates
        parent_last_year_cost += last_year_cost
        parent_last_year_kwh += last_year_kwh
        parent_last_year_dates |= last_year_dates

        diff_last_interval = None
        diff_last_year = None

        if len(current_dates) > 0 :

            current_average_cost = current_cost / len(current_dates)
            current_average_kwh = current_kwh / len(current_dates)

            if last_interval_kwh > 0 and len(last_interval_dates) > 0:

                last_interval_average_kwh = last_interval_kwh / len(last_interval_dates)
                diff_last_interval = (current_average_kwh - last_interval_average_kwh)*100/last_interval_average_kwh

            if last_year_kwh > 0 and len(last_year_dates) > 0:

                last_year_average_kwh = last_year_kwh / len(last_year_dates)
                diff_last_year = (current_average_kwh - last_year_average_kwh)*100/last_year_average_kwh

        else:
            current_average_cost = None

        sub_system_stat = {
            'name': sub_system['name'],
            'average_cost': current_average_cost,
            'diff_last_interval': CompareTplHepler(diff_last_interval),
            'diff_last_year': CompareTplHepler(diff_last_year),
            'color': type_colors[ix % len(type_colors)],
        }

        sub_system_stats.append(sub_system_stat)

    parent_diff_last_interval = None
    parent_diff_last_year = None
    parent_last_interval_average_kwh = 0
    parent_last_year_average_kwh = 0

    if len(parent_current_dates) > 0 :

        parent_current_average_cost = parent_current_cost / len(parent_current_dates)
        parent_current_average_kwh = parent_current_kwh / len(parent_current_dates)

        if parent_last_interval_kwh > 0 and len(parent_last_interval_dates) > 0:

            parent_last_interval_average_kwh = parent_last_interval_kwh/len(parent_last_interval_dates)
            parent_diff_last_interval = (parent_current_average_kwh - parent_last_interval_average_kwh)*100/parent_last_interval_average_kwh

        if parent_last_year_kwh > 0 and len(parent_last_year_dates) > 0:

            parent_last_year_average_kwh = parent_last_year_kwh/len(parent_last_year_dates)
            parent_diff_last_year = (parent_current_average_kwh - parent_last_year_average_kwh)*100/parent_last_year_average_kwh

    else:
        parent_current_average_cost = 0

    parent = {
        'average_cost': parent_current_average_cost,
        'diff_last_interval': CompareTplHepler(parent_diff_last_interval),
        'diff_last_year': CompareTplHepler(parent_diff_last_year),
        #'highest_cost_diff_system': highest_cost_diff_system,
    }

    return {"parent": parent, "details": sub_system_stats}


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

    weekday_usage = current_system.weekday_weekend_usage(start_dt, end_dt, "weekday")

    if len(weekday_usage['dates']) > 0:
        weekday_cost = weekday_usage['totalMoney'] / len(weekday_usage['dates'])
    else:
        weekday_cost = 0

    compare_to_last_weekday = None

    last_weekday_usage = current_system.weekday_weekend_usage(last_start_dt, last_end_dt, "weekday")

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
        if self.compared_percent is None or self.compared_percent == 0:
            return 'neutral-usage'
        elif self.compared_percent > 0:
            return 'more-usage'
        elif self.compared_percent < 0:
            return 'less-usage'

    @property
    def change_icon_path(self):
        if self.compared_percent is None:
            return 'images/reports/na.gif'

        path = 'images/reports/decrease_energy.png'
        if self.compared_percent >= 0:
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

    TYPE_COLORS = ['#68c0d4', '#8c526f', '#d5c050', '#8B8250', '#5759A7', '#6EC395', '#ee9646', '#ee5351', '#178943', '#ba1e6a', '#045a6f', '#0298bb']

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

    m['global_sub_systems'] = current_system.direct_sources_and_systems(current_lang())

    def generate_section_1_summary(system, start_date, end_date, m):
        # beginning of section 1a summary stats
        current_usage = system.total_usage(start_date, end_date)
        last_year_usage = system.total_usage(start_date - relativedelta(years=1), end_date - relativedelta(years=1))
        system_and_childs = System.get_systems_within_root(system.code)
        system_timezone = pytz.timezone(system.timezone)

        print(last_year_usage)

        grouped_baselines = BaselineUsage.get_baselines_for_systems([s.id for s in system_and_childs])


        for s in system_and_childs:
            missing_daily_usages = s.first_record - (start_date - relativedelta(years=1))

            if missing_daily_usages.days > 0:
                if missing_daily_usages.days > (end_date - start_date).days:
                    missing_start_dt = start_date - relativedelta(years=1)
                    missing_end_dt = end_date - relativedelta(years=1)
                else:
                    missing_start_dt = start_date - relativedelta(years=1)
                    missing_end_dt = s.first_record

                baselines = grouped_baselines[s.id]
                baseline_daily_usages = BaselineUsage.transform_to_daily_usages(baselines, system_timezone)

                kwh = calculation.calculate_total_baseline_energy_usage(
                            missing_start_dt.astimezone(system_timezone),
                            missing_end_dt.astimezone(system_timezone),
                            baseline_daily_usages
                        )
                if kwh > 0:
                    money_rate = system.get_unit_rate(missing_end_dt, MONEY_CATEGORY_CODE)
                    last_year_usage['totalKwh'] += kwh
                    last_year_usage['totalMoney'] += kwh*money_rate.rate

        print(last_year_usage)

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
            m['s1_css_class_energy_saving'] = 'neutral-saving'
        # end of section 1a summary stats

        # start of section 1b sub-systems bar chart and table

        sub_system_stats = []
        sub_system_jsons = []
        sources = system.sources
        source_ids = [s.id for s in sources]
        max_kwh = 0
        total_kwh = 0

        sources_current_usage = system.total_usage_by_source(start_date, end_date, source_ids)
        sources_last_year_usage = system.total_usage_by_source(start_date - relativedelta(years=1), end_date - relativedelta(years=1), source_ids)

        for ix, sub_system in enumerate(m['global_sub_systems']):

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

            max_kwh = max(current_kwh, max_kwh)

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
                'percent_base_on_max': 0,
                'color': TYPE_COLORS[ix % len(TYPE_COLORS)],
            }

            sub_system_json = {
                'category': sub_system['name'],
                'color': TYPE_COLORS[ix % len(TYPE_COLORS)],
                'value': current_kwh,
            }

            sub_system_stats.append(sub_system_stat)
            sub_system_jsons.append(sub_system_json)

        for s in sub_system_stats:
            if s['total_kwh'] and max_kwh > 0:
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
        m['global_interval_delta'] = interval_delta

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

            if report_type == "quarter":
                value = 0
                for y in range(3):
                    interval_key = (interval_start_dt + relativedelta(months=y)).strftime('%Y%m')
                    if interval_key in interval_usages:
                        value += interval_usages[interval_key]['totalKwh']
            elif interval_key in interval_usages:
                value = interval_usages[interval_key]['totalKwh']
            else:
                value = 0

            if x == 5:
                last_value = value
            if x == 4:
                compare_value = value

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
        m['global_current_daily_usage'] = current_daily_usage
        m['global_last_daily_usage'] = last_daily_usage


        system_tz = system.time_zone
        current_series = [{'name': compare_current_name, 'type': 'current', 'value': v['totalKwh'], 'datetime': int_date_to_datetime(k, system_tz)} for k, v in current_daily_usage.items()]
        last_series = [{'name': compare_last_name, 'type': 'last', 'value': v['totalKwh'], 'datetime': int_date_to_datetime(k, system_tz)} for k, v in last_daily_usage.items()]
        compare_series = current_series + last_series

        m['s2_compare_series'] = json.dumps(compare_series, cls=DjangoJSONEncoder)

        for ix, sub_system in enumerate(m['global_sub_systems']):

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
                'color': TYPE_COLORS[ix % len(TYPE_COLORS)],
                'title': sub_system['name'],
                'current_series': json.dumps([{'name': compare_current_name, 'value': v['totalKwh'], 'datetime': int_date_to_datetime(k, system_tz)} for k, v in subsys_current_daily_usage.items()], cls=DjangoJSONEncoder),
                'last_series': json.dumps([{'name': compare_last_name, 'value': v['totalKwh'], 'datetime': int_date_to_datetime(k, system_tz)} for k, v in subsys_last_daily_usage.items()], cls=DjangoJSONEncoder),
                'chart_title': chart_title
            }
            sub_system_compare_graphs.append(graph)

        m['s2_sub_system_compare_graphs'] = sub_system_compare_graphs
        return m
        # end of section 2 comparision


    def generate_section_3_comparision(system, start_date, end_date, report_type, m):

        system_tz = system.time_zone
        all_holidays = system.get_all_holidays()
        current_daily_usage = {}
        overnight_daily_usage = {}

        highest_weekday_cost = None
        highest_weekday_date = None
        highest_weekend_cost = None
        highest_weekend_date = None
        highest_overnight_cost = None
        highest_overnight_date = None


        for k, v in m['global_current_daily_usage'].items():
            current_daily_usage[str(int_date_to_timestamp(k, system_tz))] = v['totalMoney']

            dt = int_date_to_datetime(k, system_tz)
            wd = dt.weekday()

            if wd >= 0 and wd <=4 and dt.date() not in all_holidays:
                if v['totalMoney'] > highest_weekday_cost:
                    highest_weekday_cost = v['totalMoney']
                    highest_weekday_date = dt

            if (wd >= 5 and wd <=6) or dt.date() in all_holidays:
                if v['totalMoney'] > highest_weekend_cost:
                    highest_weekend_cost = v['totalMoney']
                    highest_weekend_date = dt


        for k, v in system.overnight_usage_by_day(start_date, end_date).items():
            overnight_daily_usage[str(int_date_to_timestamp(k, system_tz))] = v['totalMoney']

            if v['totalMoney'] > highest_overnight_cost:
                highest_overnight_cost = v['totalMoney']
                highest_overnight_date = int_date_to_datetime(k, system_tz)

            if (wd >= 5 and wd <=6) or dt.date() in all_holidays:
                if v['totalMoney'] > highest_weekend_cost:
                    highest_weekend_cost = v['totalMoney']
                    highest_weekend_date = dt

        m['s3_current_daily_usage'] = json.dumps(current_daily_usage, cls=DjangoJSONEncoder)
        m['s3_overnight_daily_usage'] = json.dumps(overnight_daily_usage, cls=DjangoJSONEncoder)

        m['s3_holidays_json'] = json.dumps([d.strftime('%Y-%m-%d') for d in all_holidays])

        m['s3_highest_weekday_cost'] = highest_weekday_cost
        m['s3_highest_weekday_date'] = highest_weekday_date
        m['s3_highest_weekend_cost'] = highest_weekend_cost
        m['s3_highest_weekend_date'] = highest_weekend_date
        m['s3_highest_overnight_cost'] = highest_overnight_cost
        m['s3_highest_overnight_date'] = highest_overnight_date

        m['s3_weekday'] = generate_weekday_weekend_overnight_details(system, start_date, end_date, m["global_interval_delta"], m["global_sub_systems"], TYPE_COLORS, 'weekday')
        m['s3_weekend'] = generate_weekday_weekend_overnight_details(system, start_date, end_date, m["global_interval_delta"], m["global_sub_systems"], TYPE_COLORS, 'weekend')
        m['s3_overnight'] = generate_weekday_weekend_overnight_details(system, start_date, end_date, m["global_interval_delta"], m["global_sub_systems"], TYPE_COLORS, 'overnight')

        # Get the highest date systems usage
        if highest_weekday_date:
            highest_weekday_usage = generate_weekday_weekend_overnight_details(system, highest_weekday_date, highest_weekday_date + relativedelta(days=1), m["global_interval_delta"], m["global_sub_systems"], TYPE_COLORS, 'weekday')
        else:
            highest_weekday_usage = {'details': []}

        if highest_weekend_date:
            highest_weekend_usage = generate_weekday_weekend_overnight_details(system, highest_weekend_date, highest_weekend_date + relativedelta(days=1), m["global_interval_delta"], m["global_sub_systems"], TYPE_COLORS, 'weekend')
        else:
            highest_weekend_usage = {'details': []}

        if highest_overnight_date:
            highest_overnight_usage = generate_weekday_weekend_overnight_details(system, highest_overnight_date, highest_overnight_date + relativedelta(days=1), m["global_interval_delta"], m["global_sub_systems"], TYPE_COLORS, 'overnight')
        else:
            highest_overnight_usage = {'details': []}

        weekday_diff = 0
        highest_date_weekday_system = None
        weekend_diff = 0
        highest_date_weekend_system = None
        overnight_diff = 0
        highest_date_overnight_system = None

        for avg in m['s3_weekday']['details']:
            for highest in highest_weekday_usage['details']:
                if avg['name'] == highest['name'] and highest['average_cost'] and avg['average_cost'] and highest['average_cost'] - avg['average_cost'] > weekday_diff:
                    weekday_diff = highest['average_cost'] - avg['average_cost']
                    highest_date_weekday_system = highest['name']

        for avg in m['s3_weekend']['details']:
            for highest in highest_weekend_usage['details']:
                if avg['name'] == highest['name'] and highest['average_cost'] and avg['average_cost'] and highest['average_cost'] - avg['average_cost'] > weekend_diff:
                    weekend_diff = highest['average_cost'] - avg['average_cost']
                    highest_date_weekend_system = highest['name']

        for avg in m['s3_overnight']['details']:
            for highest in highest_overnight_usage['details']:
                if avg['name'] == highest['name'] and highest['average_cost'] and avg['average_cost'] and highest['average_cost'] - avg['average_cost'] > overnight_diff:
                    overnight_diff = highest['average_cost'] - avg['average_cost']
                    highest_date_overnight_system = highest['name']

        m['s3_weekday']['parent']['highest_date_highest_diff_system'] = highest_date_weekday_system
        m['s3_weekend']['parent']['highest_date_highest_diff_system'] = highest_date_weekend_system
        m['s3_overnight']['parent']['highest_date_highest_diff_system'] = highest_date_overnight_system

        # m['s3_overnight'] = generate_weekday_weekend_details(system, start_date, end_date, m["global_interval_delta"], m["global_sub_systems"], TYPE_COLORS, 'weekday')

        return m

    m = generate_section_1_summary(current_system, report_date, report_end_date + relativedelta(days=1), m)
    m = generate_section_2_comparision(current_system, report_date, report_end_date + relativedelta(days=1), report_type, m)
    m = generate_section_3_comparision(current_system, report_date, report_end_date + relativedelta(days=1), report_type, m)

    m['report_start'] = report_date
    m['report_end'] = report_end_date

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

    m['s3_overnight_timerange_text'] = "{0} - {1}".format(
        tmpDateStart.strftime('%l%p').strip(),
        tmpDateEnd.strftime('%l%p').strip(),)

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
