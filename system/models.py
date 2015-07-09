import os
import datetime
import json
import pytz
import operator
import copy

from bson.objectid import ObjectId
from collections import OrderedDict
from django.db import models
from django.db.models import Q
from django.utils import translation
from django.utils import dateparse
from dateutil.relativedelta import relativedelta
from mongoengine import connection, Q as MQ

from egauge.models import Source, SourceReadingYear, SourceReadingMonth, SourceReadingDay, SourceReadingHour, SourceReadingMin
from entrak.settings import BASE_DIR, LANG_CODE_EN, LANG_CODE_TC
from holiday.models import CityHoliday, Holiday
from unit.models import UnitRate, UnitCategory, CO2_CATEGORY_CODE, MONEY_CATEGORY_CODE
from meters.models import Electricity, HourDetail

from system.constants import CITY_ALL
from system.constants import CORPORATE
from system.constants import EDUCATION
from system.constants import COMPANY_TYPES
from system.constants import DEFAULT_NIGHT_TIME_END
from system.constants import DEFAULT_NIGHT_TIME_START
from system.constants import SOURCE_TZ_HK


UNIT_IMG_DIR = os.path.join(BASE_DIR, 'entrak', 'static', 'images', 'unit')

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
    company_type = models.PositiveIntegerField(choices=COMPANY_TYPES, default=CORPORATE)
    first_record = models.DateTimeField()
    night_time_start = models.TimeField(default=DEFAULT_NIGHT_TIME_START)
    night_time_end = models.TimeField(default=DEFAULT_NIGHT_TIME_END)
    login_required = models.BooleanField(default=True)
    unit_info = models.TextField(default='{}')
    version = models.CharField(max_length=20, choices=(('3.0', '3.0'), ('4.0', '4.0'),), null=True, blank=True)

    objects = models.Manager()


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


    @property
    def fullname(self):
        lang = translation.get_language()
        fn = self.full_name_tc if lang == 'zh-tw' else self.full_name
        return fn


    @property
    def time_zone(self):
        return pytz.timezone(self.timezone)


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


    @property
    def direct_sources(self):
        return Source.objects.filter(system_code=self.code)


    @property
    def child_systems(self):

        if self.path:
            path = '%s%s,'%(self.path,self.code)
        else:
            path = ',%s,'%self.code

        systems = System.objects.filter(path=path).order_by('path', 'name')

        return systems

    @property
    def is_corporate(self):
        return self.company_type == CORPORATE


    @property
    def is_education(self):
        return self.company_type == EDUCATION


    @property
    def money_unit(self):
        return UnitCategory.electric_units.filter(Q(city=self.city)&Q(code=MONEY_CATEGORY_CODE)).first()


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


    def direct_sources_and_systems(self, lang):

        sub_systems = []
        child_systems = self.child_systems
        direct_sources = self.direct_sources

        for s in child_systems:
            if lang == "zh-tw":
                name = s.name_tc
            else:
                name = s.name
            sub_systems.append({"id": s.id, "name": name, "object": s})

        for s in direct_sources:
            if lang == "zh-tw":
                name = s.d_name_tc
            else:
                name = s.d_name
            sub_systems.append({"id": s.id, "name": name, "object": s})

        sub_systems = sorted(sub_systems, key=lambda k: k['name'])
        return sub_systems


    def get_overnight_dates(self, start_dt, end_dt):

        current_tz = pytz.timezone(self.timezone)
        start_dt = start_dt.astimezone(current_tz)
        end_dt = end_dt.astimezone(current_tz)

        if self.night_time_start.hour <= 12:
            return start_dt.replace(hour=self.night_time_start.hour) + relativedelta(days=1), end_dt + relativedelta(hours=self.night_time_end.hour)
        else:
            return start_dt.replace(hour=self.night_time_start.hour), end_dt + relativedelta(hours=self.night_time_end.hour)


    def validate_overnight(self, dt):

        # overnight cost for Monday is defined as Monday night to Tuesday Morning
        # may actually do not include Monday usage if nighttime start is set to 00:00am afterwards

        current_tz = pytz.timezone(self.timezone)
        datetime_in_current_tz = dt.astimezone(current_tz)

        night_start_hour_min = self.night_time_start.hour*100 + self.night_time_start.minute
        night_end_hour_min = self.night_time_end.hour*100 + self.night_time_end.minute
        datetime_hour_min = datetime_in_current_tz.hour*100 + datetime_in_current_tz.minute

        if night_start_hour_min < night_end_hour_min:
            # datetime_in_current_tz BETWEEN the night time start and end hours
            # prevent miscalcuation when night time start is after 00:00am
            if (night_start_hour_min <= datetime_hour_min < night_end_hour_min):
                return datetime_in_current_tz.date() - relativedelta(days=1)
        else:
            if datetime_hour_min >= night_start_hour_min:
                return datetime_in_current_tz.date()
            elif datetime_hour_min < night_end_hour_min:
                return datetime_in_current_tz.date() - relativedelta(days=1)

        return None


    def get_unit_rate(self, datetime, target_unit=MONEY_CATEGORY_CODE):
        unit_infos = json.loads(self.unit_info)
        unit_code = unit_infos[target_unit]
        unit_rate = UnitRate.objects.filter(category_code=target_unit, code=unit_code, effective_date__lte=datetime).order_by('-effective_date').first()
        return unit_rate


    def get_unitrates(self, start_from=None, end_to=None, target_unit=MONEY_CATEGORY_CODE):
        unit_infos = json.loads(self.unit_info)
        unit_code = unit_infos[target_unit]
        kwargs = {}

        if start_from is not None:
            kwargs['effective_date__gte'] = start_from

        if end_to is not None:
            kwargs['effective_date__lte'] = end_to

        unit_rates = UnitRate.objects.filter(category_code=target_unit, code=unit_code, **kwargs).order_by('effective_date')
        return unit_rates


    def get_total_co2(self, start_dt, end_dt, date_type='day'):
        """
        Calculate the co2 usage between the dates of the system.
        """
        source_ids = [s.id for s in self.sources]

        reading_map = {
            'day': SourceReadingHour,
            'hour': SourceReadingHour,
            'week': SourceReadingDay,
            'month': SourceReadingMonth,
            'quarter': SourceReadingMonth,
            'year': SourceReadingYear,
            'custom': SourceReadingDay
        }

        reading_cls = reading_map[date_type]

        readings = reading_cls.objects(
            source_id__in=source_ids,
            datetime__gte=start_dt,
            datetime__lt=end_dt)

        if readings:
            return sum([self.get_unit_rate(r.datetime, 'co2').rate*r.value for r in readings])
        else:
            return 0

    def get_total_kwh(self, start_date, end_date):
        mdb_conn = connection.get_db()
        source_ids = [s.id for s in self.sources]

        reading = mdb_conn.source_reading_day.aggregate([
            {'$match': {
                'source_id': {'$in': source_ids},
                'datetime': {
                    '$gte': start_date,
                    '$lt': end_date
                }
            }},
            {'$group': {
                '_id': None,
                'kwh': {'$sum': '$value'}
            }}
        ])

        if reading['result']:
            return reading['result'][0]['kwh']
        else:
            return 0


    def get_total_cost(self, start_dt, end_dt, date_type='day'):
        """
        Calculate the cost between the dates of the system.
        """
        source_ids = [s.id for s in self.sources]

        reading_map = {
            'day': SourceReadingHour,
            'hour': SourceReadingHour,
            'week': SourceReadingDay,
            'month': SourceReadingMonth,
            'quarter': SourceReadingMonth,
            'year': SourceReadingYear,
            'custom': SourceReadingDay
        }

        reading_cls = reading_map[date_type]

        readings = reading_cls.objects(
            source_id__in=source_ids,
            datetime__gte=start_dt,
            datetime__lt=end_dt)

        if readings:
            return sum([self.get_unit_rate(r.datetime, 'money').rate*r.value for r in readings])
        else:
            return 0


    def get_total_cost_with_source_id(self, start_dt, end_dt):

        readings = SourceReadingHour.total_used_with_source_id([s.id for s in self.sources], start_dt, end_dt)
        rate = self.get_unit_rate(end_dt, 'money').rate

        if readings:
            return [({"source_id": r["_id"], "cost": rate*r["total"]}) for r in readings]
        else:
            return []


    def weekday_cost_by_day(self, start_dt, end_dt):

        source_ids = [str(source.id) for source in self.sources]
        system_tz = self.time_zone
        all_holidays = self.get_all_holidays()

        if isinstance(start_dt, str):
            start_dt = dateparse.parse_date(start_dt)
            start_dt = datetime.datetime.combine(start_dt, datetime.datetime.min.time())
            start_dt = system_tz.localize(start_dt)

        if isinstance(end_dt, str):
            end_dt = dateparse.parse_date(end_dt)
            end_dt = datetime.datetime.combine(end_dt, datetime.datetime.min.time())
            end_dt = system_tz.localize(end_dt)

        unit_infos = json.loads(self.unit_info)
        money_unit_rates = []
        for ur in UnitRate.objects.filter(category_code='money', code=unit_infos['money']).order_by('-effective_date'):
            money_unit_rates.append({"date": ur.effective_date.astimezone(system_tz).strftime("%Y-%m-%d"), "rate": ur.rate})

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

            reading_datetime = reading["_id"].astimezone(system_tz)

            if reading_datetime.weekday() <= 4 and reading_datetime.date() not in all_holidays:

                for ur in money_unit_rates:
                    if reading_datetime.strftime("%Y-%m-%d") >= ur["date"]:
                        rate = ur["rate"]
                        break

                weekday_costs.append({'date':reading_datetime.strftime("%Y-%m-%d"), 'weekday':reading_datetime, 'value':reading["value"]*rate})
                total_days += 1
                total_values += reading["value"]*rate

        return {'data': weekday_costs, 'total': total_values, 'number_of_days': total_days}


    def overnight_cost_by_day(self, start_dt, end_dt):

        source_ids = [str(source.id) for source in self.sources]
        system_tz = pytz.timezone(self.timezone)

        unit_infos = json.loads(self.unit_info)
        money_unit_rates = []
        for ur in UnitRate.objects.filter(category_code='money', code=unit_infos['money']).order_by('-effective_date'):
            money_unit_rates.append({"date": ur.effective_date.astimezone(system_tz).strftime("%Y-%m-%d"), "rate": ur.rate})

        overnight_start_dt, overnight_end_dt = self.get_overnight_dates(start_dt, end_dt)

        costs = {}
        current_db_conn = connection.get_db()
        readings = current_db_conn.source_reading_hour.aggregate([
                { "$match":
                    {
                        "source_id": {"$in": [ObjectId(s) for s in source_ids]},
                        "datetime": {"$gte": overnight_start_dt, "$lt": overnight_end_dt}
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

            dt = self.validate_overnight(reading["_id"]["datetime"])
            reading_datetime = reading["_id"]["datetime"].astimezone(system_tz)

            if dt:
                key = dt.strftime("%Y-%m-%d")
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
            dt = system_tz.localize(datetime.datetime.strptime(k, "%Y-%m-%d"))
            overnight_costs.append({'date':k, 'weekday':dt, 'value':v})
        return {'data': overnight_costs, 'total': total_values, 'number_of_days': total_days}


    def convert_to_meter_ds(self, start_dt, end_dt):

        print('{0:-^80}'.format(' %s convert_to_meter_ds(%s, %s) called '%(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),start_dt.strftime('%Y-%m-%d %H:%M:%S'),end_dt.strftime('%Y-%m-%d %H:%M:%S'))))
        started_at = datetime.datetime.now()

        source_ids = [s.id for s in self.direct_sources]
        system_tz = pytz.timezone(self.timezone)

        # start_dt should be before first_record
        if self.first_record > start_dt:
            start_dt = self.first_record
        # conversion is hour based, minutes and seconds are meaningless
        start_dt = start_dt.replace(minute=0, second=0, microsecond=0)
        end_dt = end_dt.replace(minute=0, second=0, microsecond=0)

        hours = int((end_dt - start_dt).total_seconds()/3600)

        create_count = 0
        update_count = 0

        hour_detail = HourDetail()
        total_minute_count = SourceReadingMin.objects(
            source_id__in=source_ids,
            datetime__gte=start_dt,
            datetime__lt=end_dt
        )

        if total_minute_count == 0:
            return (create_count, update_count)

        for i in range(60):
            hour_detail['m%02d'%i] = 0.00

        for i in range(hours):

            current_dt = end_dt - relativedelta(hours=i+1)
            print('{0:-^80}'.format(' %s: processing hour %s '%(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),current_dt.strftime('%Y-%m-%d %H:%M'))))

            for source_id in source_ids:

                minutes = SourceReadingMin.objects(
                    source_id=source_id,
                    datetime__gte=current_dt,
                    datetime__lt=current_dt + relativedelta(hours=1)).order_by('datetime')

                if len(minutes) == 0:
                    continue

                overnight_date = self.validate_overnight(current_dt.astimezone(system_tz))
                unit_rate_co2 = self.get_unit_rate(current_dt, CO2_CATEGORY_CODE)
                unit_rate_money = self.get_unit_rate(current_dt, MONEY_CATEGORY_CODE)

                try:
                    e = Electricity.objects.get(
                            system_id = self.id,
                            datetime_utc = current_dt,
                            source_id = source_id,
                        )
                    newly_created = False
                except Electricity.DoesNotExist:
                    e = Electricity(
                            system_id = self.id,
                            datetime_utc = current_dt,
                            source_id = source_id,
                        )
                    newly_created = True

                e.total = 0
                e.datetime_local = current_dt.replace(tzinfo=pytz.utc)
                e.local_date = int(current_dt.astimezone(system_tz).strftime("%Y%m%d"))
                e.overnight_total = 0

                if overnight_date:
                    e.overnight_date = int(overnight_date.strftime("%Y%m%d"))

                e.hour_detail = copy.deepcopy(hour_detail)
                e.rate_co2 = unit_rate_co2.rate
                e.rate_money = unit_rate_money.rate

                for m in minutes:
                    overnight = self.validate_overnight(m.datetime.astimezone(system_tz))

                    if m.value > 0:
                        e.total += m.value
                        e.hour_detail['m%02d'%m.datetime.minute] = m.value

                    if overnight:
                        e.overnight_total = e.total

                e.is_data_completed = (len(minutes) == 60)

                if e.total > 0 :
                    e.save()
                    if newly_created:
                        create_count += 1
                    else:
                        update_count += 1

        print('{0:-^80}'.format(' started at: %s, finished at : %s '%(started_at.strftime('%Y-%m-%d %H:%M:%S'), datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))
        return (create_count, update_count)


    def overnight_usage(self, start_dt, end_dt, source_ids=None):

        # print('{0:-^80}'.format(' overnigh_avg_cost called '))
        # print('{0:-^80}'.format(' start_dt: ' + start_dt.strftime('%Y-%m-%d %H:%M:%S') + ' | end_dt: ' + end_dt.strftime('%Y-%m-%d %H:%M:%S') + ' '))

        current_db_conn = Electricity._get_db()

        int_start_dt = int(start_dt.strftime("%Y%m%d"))
        int_end_dt = int(end_dt.strftime("%Y%m%d"))

        if source_ids:
            object_ids = [ObjectId(s) for s in source_ids]
        else:
            object_ids = [s.id for s in self.sources]

        system_ids = [s.id for s in System.get_systems_within_root(self.code)]

        aggregate_pipeline = [
            { "$match":
                {"$and": [
                    {"overnight_date": {"$gte": int_start_dt}},
                    {"overnight_date": {"$lt": int_end_dt}},
                    {"system_id": {"$in": system_ids}},
                    {"source_id": {"$in": object_ids}},
                ]}},
            { "$project": {"_id": 1, "overnight_date": 1, "overnight_total": 1, "rate_co2": 1, "rate_money": 1,}},
            {
                "$group": {
                    "_id" : None,
                    "dates": {"$addToSet": "$overnight_date"},
                    "totalKwh": {"$sum": "$overnight_total"},
                    "totalCo2": {"$sum": {"$multiply": ["$overnight_total", "$rate_co2"]}},
                    "totalMoney": {"$sum": {"$multiply": ["$overnight_total", "$rate_money"]}}
                }
            }
        ]

        result =  current_db_conn.electricity.aggregate(aggregate_pipeline)

        if result['result']:
            return result['result'][0]
        else:
            return {"dates": [], "totalKwh": 0, "totalCo2": 0, "totalMoney": 0}


    def total_usage(self, start_dt, end_dt, source_ids=None):

        current_db_conn = Electricity._get_db()

        if source_ids:
            object_ids = [ObjectId(s) for s in source_ids]
        else:
            object_ids = [s.id for s in self.sources]

        system_ids = [s.id for s in System.get_systems_within_root(self.code)]

        minute = end_dt.minute
        end_dt = end_dt.replace(minute=0, second=0, microsecond=0)

        aggregate_pipeline = [
            { "$match":
                {"$and": [
                    {"datetime_utc": {"$gte": start_dt}},
                    {"datetime_utc": {"$lt": end_dt}},
                    {"system_id": {"$in": system_ids}},
                    {"source_id": {"$in": object_ids}},
                ]}},
            { "$project": {"total": 1, "rate_co2": 1, "rate_money": 1, "local_date": 1,}},
            {
                "$group": {
                    "_id": None,
                    "dates": {"$addToSet": "$local_date"},
                    "totalKwh": {"$sum": "$total"},
                    "totalCo2": {"$sum": {"$multiply": ["$total", "$rate_co2"]}},
                    "totalMoney": {"$sum": {"$multiply": ["$total", "$rate_money"]}},
                }
            }
        ]

        result =  current_db_conn.electricity.aggregate(aggregate_pipeline)

        if result['result']:
            total = result['result'][0]
        else:
            total = {"dates": [], "totalKwh": 0, "totalCo2": 0, "totalMoney": 0}

        usages = Electricity.objects.filter(datetime_utc=end_dt, system_id__in=system_ids, source_id__in=object_ids)

        for u in usages:
            minute_usage = u.usage_up_to_minute(minute)
            total["totalKwh"] += minute_usage["totalKwh"]
            total["totalCo2"] += minute_usage["totalCo2"]
            total["totalMoney"] += minute_usage["totalMoney"]

        return total


    def total_usage_by_source_id(self, start_dt, end_dt, source_ids=None):

        # print('{0:-^80}'.format(' start_dt: ' + start_dt.strftime('%Y-%m-%d %H:%M:%S') + ' | end_dt: ' + end_dt.strftime('%Y-%m-%d %H:%M:%S') + ' '))

        current_db_conn = Electricity._get_db()

        if source_ids:
            object_ids = [ObjectId(s) for s in source_ids]
            sources = Source.objects(id__in=object_ids)
        else:
            sources = self.sources
            object_ids = [s.id for s in sources]

        system_ids = [s.id for s in System.get_systems_within_root(self.code)]

        minute = 0
        minute = end_dt.minute
        end_dt = end_dt.replace(minute=0, second=0, microsecond=0)

        aggregate_pipeline = [
            { "$match":
                {"$and": [
                    {"datetime_utc": {"$gte": start_dt}},
                    {"datetime_utc": {"$lt": end_dt}},
                    {"system_id": {"$in": system_ids}},
                    {"source_id": {"$in": object_ids}},
                ]}},
            { "$project": {"_id": 1, "source_id": 1, "total": 1, "rate_co2": 1, "rate_money": 1, "local_date": 1,}},
            {
                "$group": {
                    "_id": "$source_id",
                    "dates": {"$addToSet": "$local_date"},
                    "totalKwh": {"$sum": "$total"},
                    "totalCo2": {"$sum": {"$multiply": ["$total", "$rate_co2"]}},
                    "totalMoney": {"$sum": {"$multiply": ["$total", "$rate_money"]}},
                }
            }
        ]

        result =  current_db_conn.electricity.aggregate(aggregate_pipeline)

        total = {}

        if result['result']:
            for r in result['result']:
                total[r['_id']] =   {
                                        "dates": r['dates'],
                                        "totalKwh": r['totalKwh'],
                                        "totalCo2": r['totalCo2'],
                                        "totalMoney": r['totalMoney'],
                                    }

        usages = Electricity.objects.filter(datetime_utc=end_dt, system_id__in=system_ids, source_id__in=object_ids)

        for u in usages:
            minute_usage = u.usage_up_to_minute(minute)

            if u.source_id not in total:
                total[u.source_id] = {"dates": [u.local_date], "totalKwh": 0, "totalCo2": 0, "totalMoney": 0}

            total[u.source_id]["totalKwh"] += minute_usage["totalKwh"]
            total[u.source_id]["totalCo2"] += minute_usage["totalCo2"]
            total[u.source_id]["totalMoney"] += minute_usage["totalMoney"]

        return total


    def total_weekday_weekend_usage(self, start_dt, end_dt, weekday_weekend="weekday", source_ids=None):

        current_db_conn = Electricity._get_db()

        if source_ids:
            object_ids = [ObjectId(s) for s in source_ids]
        else:
            object_ids = [s.id for s in self.sources]

        holidays = [h for h in self.get_all_holidays() if h >= start_dt.date() and h < end_dt.date()]
        holidays = [int(h.strftime("%Y%m%d")) for h in holidays]

        if weekday_weekend != "weekday":
            days = [1,7]
            holidays_filter = {"$in": holidays}
        else:
            days = [2,3,4,5,6]
            holidays_filter = {"$nin": holidays}


        system_ids = [s.id for s in System.get_systems_within_root(self.code)]

        minute = end_dt.minute
        end_dt = end_dt.replace(minute=0, second=0, microsecond=0)

        aggregate_pipeline = [{
            "$match": {
                "$and": [
                    {"datetime_local": {"$gte": start_dt.replace(tzinfo=pytz.utc)}},
                    {"datetime_local": {"$lt": end_dt.replace(tzinfo=pytz.utc)}},
                    {"local_date": holidays_filter},
                    {"system_id": {"$in": system_ids}},
                    {"source_id": {"$in": object_ids}},
                ]
            }}, {
            "$project": {
                "total": 1,
                "rate_co2": 1,
                "rate_money": 1,
                "datetime_local": 1,
                "local_date": 1,
                "dow": {"$dayOfWeek": "$datetime_local"},
            }}, {
            "$match": {
                "dow": {"$in": days},
            }}, {
            "$group": {
                "_id": None,
                "dates": {"$addToSet": "$local_date"},
                "totalKwh": {"$sum": "$total"},
                "totalCo2": {"$sum": {"$multiply": ["$total", "$rate_co2"]}},
                "totalMoney": {"$sum": {"$multiply": ["$total", "$rate_money"]}},
            }
        }]

        result =  current_db_conn.electricity.aggregate(aggregate_pipeline)
        if result['result']:
            total = result['result'][0]
        else:
            total = {"dates": [], "totalKwh": 0, "totalCo2": 0, "totalMoney": 0}

        usages = Electricity.objects.filter(datetime_utc=end_dt, system_id__in=system_ids, source_id__in=object_ids)

        for u in usages:
            minute_usage = u.usage_up_to_minute(minute)
            total["totalKwh"] += minute_usage["totalKwh"]
            total["totalCo2"] += minute_usage["totalCo2"]
            total["totalMoney"] += minute_usage["totalMoney"]

        return total


    def total_usage_by_interval(self, start_dt, end_dt, interval="MONTH", source_ids=None):

        # print('{0:-^80}'.format(' start_dt: ' + start_dt.strftime('%Y-%m-%d %H:%M:%S') + ' | end_dt: ' + end_dt.strftime('%Y-%m-%d %H:%M:%S') + ' '))

        current_db_conn = Electricity._get_db()

        if source_ids:
            object_ids = [ObjectId(s) for s in source_ids]
            sources = Source.objects(id__in=object_ids)
        else:
            sources = self.sources
            object_ids = [s.id for s in sources]

        system_ids = [s.id for s in System.get_systems_within_root(self.code)]

        minute = 0
        minute = end_dt.minute
        end_dt = end_dt.replace(minute=0, second=0, microsecond=0)
        end_dt_local = end_dt.astimezone(self.time_zone) - relativedelta(microseconds=1)

        if interval == 'DAY':
            project_interval = "$local_date"
            key = int(end_dt_local.strftime('%Y%m%d'))
        elif interval == 'MONTH':
            project_interval = {"$month": "$datetime_local"}
            key = end_dt_local.month
        elif interval == 'WEEK':
            project_interval = {"$week": "$datetime_local"}
            key = int(end_dt_local.strftime('%U'))
        elif interval == 'QUARTER':
            project_interval = {"$dateToString": {"format": "%Y%m", "date": "$datetime_local"}}
            key = end_dt_local.strftime('%Y%m')
        elif interval == 'YEAR':
            project_interval = {"$year": "$datetime_local"}
            key = end_dt_local.year
        else:
            project_interval = {"$month": "$datetime_local"}
            key = end_dt_local.month

        aggregate_pipeline = [
            { "$match": { "$and": [
                        {"datetime_utc": {"$gte": start_dt}},
                        {"datetime_utc": {"$lt": end_dt}},
                        {"system_id": {"$in": system_ids}},
                        {"source_id": {"$in": object_ids}},
            ]}},
            { "$project": {
                "total": 1,
                "rate_co2": 1,
                "rate_money": 1,
                "local_date": 1,
                "interval": project_interval,
            }},
            { "$group": {
                "_id": {"interval": "$interval"},
                "dates": {"$addToSet": "$local_date"},
                "totalKwh": {"$sum": "$total"},
                "totalCo2": {"$sum": {"$multiply": ["$total", "$rate_co2"]}},
                "totalMoney": {"$sum": {"$multiply": ["$total", "$rate_money"]}},
            }}
        ]

        result =  current_db_conn.electricity.aggregate(aggregate_pipeline)

        total = {}

        if result['result']:
            for r in result['result']:
                total[r['_id']['interval']] =   {
                        "dates": r['dates'],
                        "totalKwh": r['totalKwh'],
                        "totalCo2": r['totalCo2'],
                        "totalMoney": r['totalMoney'],
                    }

        usages = Electricity.objects.filter(datetime_utc=end_dt, system_id__in=system_ids, source_id__in=object_ids)

        for u in usages:
            minute_usage = u.usage_up_to_minute(minute)

            if key not in total:
                total[key] = {"dates": [u.local_date], "totalKwh": 0, "totalCo2": 0, "totalMoney": 0}

            total[key]["totalKwh"] += minute_usage["totalKwh"]
            total[key]["totalCo2"] += minute_usage["totalCo2"]
            total[key]["totalMoney"] += minute_usage["totalMoney"]

        return total


class SystemHomeImage(models.Model):
    image = models.ImageField(upload_to="system_home/%Y/%m")
    system = models.ForeignKey(System)
