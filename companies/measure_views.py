import datetime, pytz

from mongoengine import connection
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

        date_start = datetime.datetime.now(pytz.utc).replace(
            hour=0, minute=0, second=0, microsecond=0)
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
