import datetime, pytz
import time

from mongoengine import connection

from django.utils import dateparse
from rest_framework import generics, mixins

from system.models import System
from egauge.models import SourceReadingYear, SourceReadingMonth, SourceReadingDay, SourceReadingHour, SourceReadingMin, Source
from .serializers import MeasureSerializer

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


class EnergyUsedRetrieve(generics.RetrieveAPIView):

    serializer_class = MeasureSerializer


    def get_queryset(self):

        syscode = self.kwargs['system_code']
        sys = System.objects.get(code=syscode)
        source_ids = [s.id for s in sys.sources]

        query_dt = self.request.QUERY_PARAMS.get('datetime', None)
        query_type = self.request.QUERY_PARAMS.get('type', None)

        if query_dt is not None and query_type in ['weekly', 'monthly']:

            date = dateparse.parse_date(date)
            date_end = time.strptime(query_dt + " " + sys.time_zone, "%Y-%m-%d %H:%M:%S %Z")

            if query_type == "weekly":
              date_start = date_end.replace(hour=0, minute=0, second=0, microsecond=0) - relativedelta(days=date_end.isoweekday())
            else:
              date_start = date_end.replace(day=0, hour=0, minute=0, second=0, microsecond=0)

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
