import datetime, pytz
import time
import dateutil


from mongoengine import connection
from dateutil.relativedelta import relativedelta
from django.utils import dateparse
from rest_framework import generics, mixins

from system.models import System
from egauge.models import SourceReadingYear, SourceReadingMonth, SourceReadingDay, SourceReadingHour, SourceReadingMin, Source
from .serializers import MeasureSerializer, TotalSerializer

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

    serializer_class = MeasureSerializer


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

            mdb_conn = connection.get_db()
            current = mdb_conn.source_reading_hour.aggregate([
                { "$match":
                  {
                      "source_id": {"$in": source_ids},
                      "datetime": {"$gte": date_start, "$lt": date_end }
                  }
              },
                { "$group":
                  {
                      "_id": None,
                      "value": {"$sum": "$value"}
                  }
              }
            ])

            previous = mdb_conn.source_reading_hour.aggregate([
                { "$match":
                  {
                      "source_id": {"$in": source_ids},
                      "datetime": {"$gte": previous_date_start, "$lt": previous_date_end }
                  }
              },
                { "$group":
                  {
                      "_id": None,
                      "value": {"$sum": "$value"}
                  }
              }
            ])

            if current['result']:
                current_reading = current['result'][0]['value']*money_rate.rate
            else:
                current_reading = 0

            if previous['result']:
                previous_reading = previous['result'][0]['value']*money_rate.rate
            else:
                previous_reading = 0

            json_data = [{'datetime': date_start, 'value': current_reading}, {'datetime': previous_date_start, 'value': previous_reading}]

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

