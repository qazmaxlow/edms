import os
import datetime
import json
import pytz
import operator

from django.db import models
from django.db.models import Q
from django.utils import translation
from django.utils import dateparse

from egauge.manager import SourceManager
from egauge.models import Source, SourceReadingHour
from entrak.settings import BASE_DIR, LANG_CODE_EN, LANG_CODE_TC
from holiday.models import CityHoliday, Holiday

from mongoengine import connection, Q as MQ
from unit.models import UnitRate, CO2_CATEGORY_CODE, MONEY_CATEGORY_CODE

SOURCE_TZ_HK = u'Asia/Hong_Kong'
UNIT_IMG_DIR = os.path.join(BASE_DIR, 'entrak', 'static', 'images', 'unit')
CITY_ALL = 'all'

DEFAULT_NIGHT_TIME_START = datetime.time(22)
DEFAULT_NIGHT_TIME_END = datetime.time(7)

class ReportManager(models.Manager):

    def get_unitrate_by_source_id(source_id, datetime):

        source = Source.objects(id=str(source_id)).first()
        system = System.objects.get(code=source.system_code)
        unit_infos = json.loads(system.unit_info)
        money_unit_code = unit_infos['money']
        money_unit_rates = UnitRate.objects.filter(category_code='money', code=unit_infos['money'])
        dt = datetime
        ur = money_unit_rates.filter(effective_date__lte=dt).order_by('-effective_date').first()
        return ur

    def __average_weekday_cost(source_id, source_reading):

        total_day = 0
        total_val = 0

        all_holidays = current_system.get_all_holidays()

        for t, v in source_reading.items():
            dt = datetime.datetime.fromtimestamp(t, current_system_tz)
            if dt.weekday() <= 4 or dt.date() in all_holidays:
                # total_val += get_unit_rate(source_id, t).rate * v
                total_val += v
                total_day += 1

        if total_day > 0:
            return total_val / float(total_day)

    def weekday_cost_by_day(self, current_system, start_dt, end_dt):

        sources = SourceManager.get_sources(current_system)
        source_ids = [str(source.id) for source in sources]
        current_system_tz = pytz.timezone(current_system.timezone)

        if isinstance(start_dt, str):
            start_dt = dateparse.parse_date(start_dt)
            start_dt = datetime.datetime.combine(start_dt, datetime.datetime.min.time())
            start_dt = current_system_tz.localize(start_dt)

        if isinstance(start_dt, str):
            end_dt = dateparse.parse_date(end_dt)
            end_dt = datetime.datetime.combine(end_dt, datetime.datetime.min.time())
            end_dt = current_system_tz.localize(end_dt)

        day_source_readings = SourceManager.get_readings_with_target_class(source_ids, SourceReadingDay, start_dt, end_dt)

        if day_source_readings:
            weekday_costs = [(source_id, __average_weekday_cost(source_id, sr) ) for source_id, sr in day_source_readings.items()]
            return sum([ c*get_unitrate_by_source_id(s,) for s, c in weekday_costs if c is not None])

    def overnight_cost_by_day(self, current_system, start_dt, end_dt):

        sources = SourceManager.get_sources(current_system)
        source_ids = [str(source.id) for source in sources]
        current_system_tz = pytz.timezone(current_system.timezone)

        if isinstance(start_dt, str):
            start_dt = dateparse.parse_date(start_dt)
            start_dt = datetime.datetime.combine(start_dt, datetime.datetime.min.time())
            start_dt = current_system_tz.localize(start_dt)

        if isinstance(end_dt, str):
            end_dt = dateparse.parse_date(end_dt)
            end_dt = datetime.datetime.combine(end_dt, datetime.datetime.min.time())
            end_dt = current_system_tz.localize(end_dt)

        unit_infos = json.loads(current_system.unit_info)
        money_unit_code = unit_infos['money']
        money_unit_rates = UnitRate.objects.filter(category_code='money', code=unit_infos['money']).order_by('effective_date')

        date_ranges = []
        date_with_readings = []

        for ix, mr in enumerate(money_unit_rates):
            c_rate_date = mr.effective_date.astimezone(current_system_tz)
            if c_rate_date >= start_dt and c_rate_date <= end_dt:
                try:
                    n_rate_date = money_unit_rates[ix+1].effective_date.astimezone(current_system_tz)
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
                on_sd = datetime.datetime.combine(rday, current_system.night_time_start)
                on_sd = on_sd.replace(tzinfo=current_system_tz)

                on_ed = datetime.datetime.combine(
                    rday + datetime.timedelta(days=1), current_system.night_time_end)
                on_ed = on_ed.replace(tzinfo=current_system_tz)

                q = MQ(datetime__gte=on_sd, datetime__lt=on_ed)
                mqs.append(q)

            conds = reduce(
                operator.or_,
                mqs
            )

            dr_sum = r.rate * SourceReadingHour.objects(conds, source_id__in=source_ids).sum('value')
            total_on_sum += dr_sum
            date_with_readings.append({"date": date_range, "value":dr_sum})

        # return total_on_sum / (end_dt - start_dt).days
        return date_with_readings


class System(models.Model):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=200)
    name_tc = models.CharField(max_length=200, blank=True)
    full_name = models.CharField(max_length=200, blank=True)
    full_name_tc = models.CharField(max_length=200, blank=True)
    intro = models.CharField(max_length=2000, blank=True)
    intro_tc = models.CharField(max_length=2000, blank=True)
    path = models.CharField(max_length=2000, blank=True)
    logo = models.ImageField(blank=True, upload_to="system_logo/%Y/%m")
    last_update = models.DateTimeField(auto_now=True, blank=True, null=True)
    lat = models.FloatField(default=0)
    lng = models.FloatField(default=0)
    city = models.CharField(max_length=200, default='hk')
    timezone = models.CharField(max_length=50, default=SOURCE_TZ_HK)
    population = models.PositiveIntegerField(default=1)
    first_record = models.DateTimeField()
    night_time_start = models.TimeField(default=DEFAULT_NIGHT_TIME_START)
    night_time_end = models.TimeField(default=DEFAULT_NIGHT_TIME_END)
    login_required = models.BooleanField(default=True)

    unit_info = models.TextField(default='{}')

    objects = models.Manager()
    reports = ReportManager()

    @staticmethod
    def get_systems_within_root(code):
        path = ',%s,'%code
        systems = System.objects.filter(Q(code=code) | Q(path__contains=path)).order_by('path', 'name')

        return systems

    @staticmethod
    def get_system_path_components(path, system_code, start_from_code, user_systems):
        system_path_components = [code for code in path.split(',') if code !='']
        system_path_components.append(system_code)
        start_idx = system_path_components.index(start_from_code)

        code_name_map = {}
        for system in user_systems:
            code_name_map[system.code] = {'name': system.name, 'name_tc': system.name_tc}

        result = []
        for code in system_path_components[start_idx:]:
            result.append({
                'code': code,
                'nameInfo': {
                    LANG_CODE_EN: code_name_map[code]['name'],
                    LANG_CODE_TC: code_name_map[code]['name_tc'],
                },
            })

        return result

    @staticmethod
    def get_systems_info(system_code, user_system_code):
        systems = System.get_systems_within_root(system_code)
        user_systems = System.get_systems_within_root(user_system_code)
        system_path_components = System.get_system_path_components(systems[0].path, systems[0].code, user_system_code, user_systems)

        return {'systems': systems, 'user_systems': user_systems,
            'system_path_components': system_path_components}

    @staticmethod
    def assign_source_under_system(systems, sources):
        result = {}
        for system in systems:
            match_sources = [source for source in sources if source.system_code == system.code]
            if match_sources:
                result[system] = match_sources

        return result

    def __unicode__(self):
        return "code: %s, name: %s"%(self.code, self.name)

    def get_all_holidays(self, timestamp_info=None):
        if timestamp_info:
            system_timezone = pytz.timezone(self.timezone)
            transformed_dt_ranges = []
            for name, dt_range in timestamp_info.items():
                transformed_dt_ranges.append(
                    Q(date__gte=dt_range['start'].astimezone(system_timezone).date(),
                      date__lt=dt_range['end'].astimezone(system_timezone).date())
                )
            date_bounds = reduce(operator.or_, transformed_dt_ranges)
            city_holidays = CityHoliday.objects.filter(date_bounds, city=self.city).values_list('date', flat=True)
            holidays = Holiday.objects.filter(date_bounds, system=self).values_list('date', flat=True)
        else:
            city_holidays = CityHoliday.objects.filter(city=self.city).values_list('date', flat=True)
            holidays = Holiday.objects.filter(system=self).values_list('date', flat=True)

        all_holidays = set(city_holidays).union(holidays)
        return list(all_holidays)

    @property
    def fullname(self):
        lang = translation.get_language()
        fn = self.full_name_tc if lang == 'zh-tw' else self.full_name
        return fn

class SystemHomeImage(models.Model):
    image = models.ImageField(upload_to="system_home/%Y/%m")
    system = models.ForeignKey(System)
