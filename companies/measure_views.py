import datetime, pytz

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

        measured_entries = SourceReadingHour.objects(
            source_id__in=source_ids,
            datetime__gte=date_start,
            datetime__lt=date_end
        )

        return measured_entries
