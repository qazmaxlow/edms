import os
import datetime
import json
import pytz
import operator

from bson.objectid import ObjectId
from collections import OrderedDict
from django.db import models
from django.db.models import Q
from django.utils import translation
from django.utils import dateparse
from dateutil.relativedelta import relativedelta
from mongoengine import connection, Q as MQ

from egauge.manager import SourceManager
from egauge.models import Source, SourceReadingHour, SourceReadingDay
from entrak.settings import BASE_DIR, LANG_CODE_EN, LANG_CODE_TC
from holiday.models import CityHoliday, Holiday
from unit.models import UnitRate, CO2_CATEGORY_CODE, MONEY_CATEGORY_CODE

SOURCE_TZ_HK = u'Asia/Hong_Kong'
UNIT_IMG_DIR = os.path.join(BASE_DIR, 'entrak', 'static', 'images', 'unit')
CITY_ALL = 'all'

DEFAULT_NIGHT_TIME_START = datetime.time(22)
DEFAULT_NIGHT_TIME_END = datetime.time(7)

class ReportManager(models.Manager):

    def weekday_cost_by_day(self, current_system, start_dt, end_dt):

        sources = SourceManager.get_sources(current_system)
        source_ids = [str(source.id) for source in sources]
        current_system_tz = pytz.timezone(current_system.timezone)
        all_holidays = current_system.get_all_holidays()

        if isinstance(start_dt, str):
            start_dt = dateparse.parse_date(start_dt)
            start_dt = datetime.datetime.combine(start_dt, datetime.datetime.min.time())
            start_dt = current_system_tz.localize(start_dt)

        if isinstance(end_dt, str):
            end_dt = dateparse.parse_date(end_dt)
            end_dt = datetime.datetime.combine(end_dt, datetime.datetime.min.time())
            end_dt = current_system_tz.localize(end_dt)

        unit_infos = json.loads(current_system.unit_info)
        money_unit_rates = []
        for ur in UnitRate.objects.filter(category_code='money', code=unit_infos['money']).order_by('-effective_date'):
            money_unit_rates.append({"date": ur.effective_date.astimezone(current_system_tz).strftime("%Y-%m-%d"), "rate": ur.rate})

        weekday_costs = []
        total_values = 0
        total_days = 0

        current_db_conn = connection.get_db()
        readings = current_db_conn.source_reading_day.aggregate([
                { "$match":
                    {
                        "source_id": {"$in": [ObjectId(s) for s in source_ids]},
                        "datetime": {"$gte": start_dt, "$lt": end_dt + relativedelta(days=1)}
                    }
                },
                { "$group":
                    {
                        "_id": "$datetime",
                        "value": {"$sum": "$value"}
                    }
                }
            ])
        # readings = SourceReadingDay.objects(source_id__in=source_ids, datetime__gte=start_dt, datetime__lt=(end_dt + relativedelta(days=1)))
        for reading in readings["result"]:

            reading_datetime = reading["_id"].astimezone(current_system_tz)

            if reading_datetime.weekday() <= 4 and reading_datetime.date() not in all_holidays:

                for ur in money_unit_rates:
                    if reading_datetime.strftime("%Y-%m-%d") >= ur["date"]:
                        rate = ur["rate"]
                        break

                weekday_costs.append({'date':reading_datetime.strftime("%Y-%m-%d"), 'weekday':reading_datetime.strftime("%a"), 'value':reading["value"]*rate})
                total_days += 1
                total_values += reading["value"]*rate

        return {'data': weekday_costs, 'total': total_values, 'number_of_days': total_days}

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
        money_unit_rates = []
        for ur in UnitRate.objects.filter(category_code='money', code=unit_infos['money']).order_by('-effective_date'):
            money_unit_rates.append({"date": ur.effective_date.astimezone(current_system_tz).strftime("%Y-%m-%d"), "rate": ur.rate})

        start_dt, end_dt = current_system.get_overnight_dates(start_dt, end_dt)

        costs = {}
        current_db_conn = connection.get_db()
        readings = current_db_conn.source_reading_hour.aggregate([
                { "$match":
                    {
                        "source_id": {"$in": [ObjectId(s) for s in source_ids]},
                        "datetime": {"$gte": start_dt, "$lt": end_dt}
                    }
                },
                { "$group":
                    {
                        "_id": {"datetime": "$datetime", "hour": {"$hour": "$datetime"}},
                        "value": {"$sum": "$value"}
                    }
                }
            ])

        # readings = SourceReadingHour.objects(source_id__in=source_ids, datetime__gte=start_dt, datetime__lt=(end_dt + relativedelta(days=1)))

        total_values = 0
        total_days = 0

        for reading in readings["result"]:

            dt = current_system.validate_overnight(reading["_id"]["datetime"])
            reading_datetime = reading["_id"]["datetime"].astimezone(current_system_tz)

            if dt:
                key = dt.strftime("%Y-%m-%d %a")
                for ur in money_unit_rates:
                    if reading_datetime.strftime("%Y-%m-%d") >= ur["date"]:
                        rate = ur["rate"]
                        break

                if key in costs:
                    costs[key] += reading["value"]*rate
                else:
                    costs[key] = reading["value"]*rate
                    total_days += 1

                total_values += reading["value"]*rate

        overnight_costs = []
        for k,v in OrderedDict(sorted(costs.items())).items():
            overnight_costs.append({'date':k.split(" ")[0], 'weekday':k.split(" ")[1], 'value':v})
        return {'data': overnight_costs, 'total': total_values, 'number_of_days': total_days}


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
    area_sqfoot = models.PositiveIntegerField(blank=True, null=True)
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

    def get_overnight_dates(self, start_dt, end_dt):

        current_tz = pytz.timezone(self.timezone)
        start_dt = start_dt.astimezone(current_tz)
        end_dt = end_dt.astimezone(current_tz)

        if self.night_time_start.hour <= 12:
            return start_dt.replace(hour=self.night_time_start.hour) + relativedelta(days=1), end_dt + relativedelta(days=1,hours=self.night_time_end.hour)
        else:
            return start_dt.replace(hour=self.night_time_start.hour), end_dt + relativedelta(days=1,hours=self.night_time_end.hour)

    def validate_overnight(self, datetime):

        # overnight cost for Monday is defined as Monday night to Tuesday Morning
        # may actually do not include Monday usage if nighttime start is set to 00:00am afterwards

        current_tz = pytz.timezone(self.timezone)
        datetime_in_current_tz = datetime.astimezone(current_tz)

        if self.night_time_start.hour <= 12:
            # datetime_in_current_tz BETWEEN the night time start and end hours
            # prevent miscalcuation when night time start is after 00:00am
            if (self.night_time_start.hour <=  datetime_in_current_tz.hour < self.night_time_end.hour):
                return datetime_in_current_tz.date() - relativedelta(days=1)
        else:
            if datetime_in_current_tz.hour >= self.night_time_start.hour:
                return datetime_in_current_tz.date()
            elif datetime_in_current_tz.hour < self.night_time_end.hour:
                return datetime_in_current_tz.date() - relativedelta(days=1)

        return None

    @property
    def fullname(self):
        lang = translation.get_language()
        fn = self.full_name_tc if lang == 'zh-tw' else self.full_name
        return fn

    @property
    def sources(self):
        system_code = self.code
        system_path = self.path

        if not system_path:
            target_path = ',%s,' % system_code
        else:
            target_path = '%s%s,' % (system_path, system_code)

        sources = Source.objects(
            MQ(system_code=system_code) |
            MQ(system_path__startswith=target_path
          ))

        return sources


class SystemHomeImage(models.Model):
    image = models.ImageField(upload_to="system_home/%Y/%m")
    system = models.ForeignKey(System)
