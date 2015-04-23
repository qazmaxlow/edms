import datetime, pytz
import time
import dateutil

from mongoengine import connection
from dateutil.relativedelta import relativedelta
from django.utils import dateparse
from rest_framework import generics, mixins

from system.models import System
from egauge.models import SourceReadingYear, SourceReadingMonth, SourceReadingDay, SourceReadingHour, SourceReadingMin, Source
from .serializers import MeasureSerializer, TotalSerializer, MeasureTimeSpanSerializer, TopThreeConsumersSerializer, LastWeekStatSerializer


class DailyMeasureList(generics.ListAPIView):
    serializer_class = MeasureSerializer

    def get_queryset(self):
        syscode = self.kwargs['system_code']
        sys = System.objects.get(code=syscode)
        source_ids = [s.id for s in sys.sources]

        date = self.request.QUERY_PARAMS.get('date', None)
        if date is not None:
            date = dateparse.parse_date(date)

            date_start = datetime.datetime.combine(date, datetime.datetime.min.time())
            date_start = sys.time_zone.localize(date_start)

            date_end = date_start + datetime.timedelta(days=1)

            mdb_conn = connection.get_db()
            measured_entries = mdb_conn.source_reading_hour.aggregate([
                { "$match":
                  {
                      "source_id": {"$in": source_ids},
                      "datetime": {"$gte": date_start, "$lt": date_end }
                  }
              },
                { "$group":
                  {
                      "_id": "$datetime",
                      "value": {"$sum": "$value"}
                  }
              }
            ])

            results = measured_entries['result']
            json_data = [{'datetime': m['_id'], 'value': m['value']} for m in results]

            return json_data


class EnergyUsedList(generics.ListAPIView):

    serializer_class = MeasureTimeSpanSerializer


    def get_queryset(self):

        syscode = self.kwargs['system_code']
        sys = System.objects.get(code=syscode)
        source_ids = [s.id for s in sys.sources]


        query_dt = self.request.QUERY_PARAMS.get('datetime', None)
        query_type = self.request.QUERY_PARAMS.get('type', None)

        if query_dt is not None and query_type in ['weekly', 'monthly']:

            date_end = dateutil.parser.parse(query_dt).astimezone(pytz.timezone(sys.timezone))
            money_rate = sys.get_unit_rate(date_end, 'money')

            if query_type == "weekly":
                date_start = date_end.replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=date_end.isoweekday())
                previous_date_start = date_start - datetime.timedelta(days=7)
                previous_date_end = date_end - datetime.timedelta(days=7)
            else:
                date_start = date_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                previous_date_start = date_start - relativedelta(months=1)
                previous_date_end = date_end - relativedelta(months=1)

            current = SourceReadingHour.total_used(source_ids, date_start, date_end)
            previous = SourceReadingHour.total_used(source_ids, previous_date_start, previous_date_end)

            if current:
                current_reading = current[0]['total']*money_rate.rate
            else:
                current_reading = 0

            if previous:
                previous_reading = previous[0]['total']*money_rate.rate
            else:
                previous_reading = 0

            json_data = [
                {'start_datetime': date_start, 'end_datetime': date_end, 'value': current_reading, 'is_today': True},
                {'start_datetime': previous_date_start, 'end_datetime': previous_date_end, 'value': previous_reading, 'is_today': False}
              ]

            return json_data


class TotalDetail(generics.RetrieveAPIView):
    serializer_class = TotalSerializer

    def get_object(self):
        syscode = self.kwargs['system_code']
        sys = System.objects.get(code=syscode)

        date_start = datetime.datetime.now(pytz.utc)
        date_start = datetime.datetime.combine(date_start, datetime.datetime.min.time())
        date_end = date_start + datetime.timedelta(days=1)

        _date_start = self.request.QUERY_PARAMS.get('date_start', None)
        _date_end = self.request.QUERY_PARAMS.get('date_end', None)

        if _date_start is not None:
            date_start = datetime.datetime.fromtimestamp(int(_date_start)/1000.0, tz=pytz.utc)


        if _date_end is not None:
            date_end = datetime.datetime.fromtimestamp(int(_date_end)/1000.0, tz=pytz.utc)


        total_cost = sys.get_total_cost(date_start, date_end)
        total_co2 = sys.get_total_co2(date_start, date_end)

        json_data = {'cost': total_cost, 'co2': total_co2}

        return json_data


class TopThreeConsumersList(generics.ListAPIView):

    serializer_class = TopThreeConsumersSerializer


    def get_queryset(self):

        syscode = self.kwargs['system_code']
        sys = System.objects.get(code=syscode)

        query_dt = self.request.QUERY_PARAMS.get('datetime', None)
        query_type = self.request.QUERY_PARAMS.get('type', None)

        if query_dt is not None and query_type in ['weekly', 'monthly']:

            json_data = []
            date_end = dateutil.parser.parse(query_dt).astimezone(pytz.timezone(sys.timezone))

            if query_type == "weekly":
                date_start = date_end.replace(hour=0, minute=0, second=0, microsecond=0) - datetime.timedelta(days=date_end.isoweekday())
                previous_date_start = date_start - datetime.timedelta(days=7)
                previous_date_end = date_end - datetime.timedelta(days=7)
            else:
                date_start = date_end.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                previous_date_start = date_start - relativedelta(months=1)
                previous_date_end = date_end - relativedelta(months=1)

            childs = sys.child_systems

            if childs:

                for child_sys in childs:
                    c_cost = SourceReadingDay.total_used([s.id for s in child_sys.sources], date_start, date_end)
                    p_cost = SourceReadingHour.total_used([s.id for s in child_sys.sources], date_start, date_end)

                    if c_cost:
                        cost_now = c_cost[0]['total']
                    else:
                        cost_now = None

                    if p_cost:
                        cost_before = p_cost[0]['total']
                        percentage_change = 100*((cost_now or 0) - cost_before)/float(cost_before)
                    else:
                        cost_before = None
                        percentage_change = None

                    json_data.append({'d_name': child_sys.full_name, 'd_name_tc': child_sys.full_name_tc, 'value': cost_now, 'previous_value': cost_before, 'percentage_change': percentage_change})

            else:

                current_cost = sys.get_total_cost_with_source_id(date_start, date_end)
                previous_cost = sys.get_total_cost_with_source_id(previous_date_start, previous_date_end)

                for s in sys.sources:
                    c_cost = [c for c in current_cost if c['source_id'] == s.id]
                    p_cost = [p for p in previous_cost if p['source_id'] == s.id]

                    if c_cost:
                        cost_now = c_cost[0]['cost']
                    else:
                        cost_now = None

                    if p_cost:
                        cost_before = p_cost[0]['cost']
                        percentage_change = 100*((cost_now or 0) - cost_before)/float(cost_before)
                    else:
                        cost_before = None
                        percentage_change = None

                    json_data.append({'d_name': s['d_name'], 'd_name_tc': s['d_name_tc'], 'value': cost_now, 'previous_value': cost_before, 'percentage_change': percentage_change})

            if json_data:
                json_data.sort(key=lambda r: ((-1*r['value'] if r['value'] else 0), (r['d_name'])))

            return json_data[0:3]


class LastWeekDailyCostList(generics.ListAPIView):

    serializer_class = LastWeekStatSerializer


    def get_queryset(self):

        def daterange(start_date, end_date):
            for n in range(int ((end_date - start_date).days)):
                yield start_date + datetime.timedelta(n)

        syscode = self.kwargs["system_code"]
        sys = System.objects.get(code=syscode)

        query_dt = self.request.QUERY_PARAMS.get("datetime", None)

        if query_dt is not None:

            json_data = []

            today = dateutil.parser.parse(query_dt).astimezone(sys.time_zone).replace(hour=0, minute=0, second=0, microsecond=0)

            for query_type in ["weekday", "overnight"]:
                last_week_start_dt = today - relativedelta(days=7+today.isoweekday())
                last_week_end_dt = today - relativedelta(days=today.isoweekday())

                two_weeks_ago_start_dt = last_week_start_dt - relativedelta(days=7)
                two_weeks_ago_end_dt = last_week_end_dt - relativedelta(days=7)

                if query_type == "weekday":
                    last_week_stats = sys.weekday_cost_by_day(last_week_start_dt, last_week_end_dt)
                    two_weeks_ago_stats = sys.weekday_cost_by_day(two_weeks_ago_start_dt, two_weeks_ago_end_dt)
                elif query_type == "overnight":
                    last_week_stats = sys.overnight_cost_by_day(last_week_start_dt, last_week_end_dt)
                    two_weeks_ago_stats = sys.overnight_cost_by_day(two_weeks_ago_start_dt, two_weeks_ago_end_dt)

                if last_week_stats["number_of_days"] > 0:
                    last_week_average = last_week_stats["total"]/float(last_week_stats["number_of_days"])
                else:
                    last_week_average = 0

                if two_weeks_ago_stats["number_of_days"] > 0:
                    two_weeks_ago_average = two_weeks_ago_stats["total"]/float(two_weeks_ago_stats["number_of_days"])
                else:
                    two_weeks_ago_average = 0

                if two_weeks_ago_average > 0:
                    percentage_change = (last_week_average - two_weeks_ago_average)*100/float(two_weeks_ago_average)
                else:
                    percentage_change = 0

                dates_with_data = []
                minimum = 999999
                maximum = 0

                for s in last_week_stats["data"]:
                    dates_with_data.append(s["date"])
                    minimum = min([minimum, s["value"]])
                    maximum = max([maximum, s["value"]])

                for single_date in daterange(last_week_start_dt, last_week_end_dt):
                    if (single_date.strftime("%Y-%m-%d") not in dates_with_data) \
                        and ((query_type == "overnight") or (query_type == "weekday" and single_date.weekday() <= 4)):

                        last_week_stats["data"].append({"date":single_date.strftime("%Y-%m-%d"), "weekday":single_date.strftime("%a"), "value":0})

                last_week_stats["data"].sort(key=lambda r: r['date'])
                json_data.append({"is_weekday": query_type == "weekday", "average": last_week_average, "minimum": minimum, "maximum": maximum, "percentage_change": percentage_change, "data": last_week_stats["data"]})

            return json_data