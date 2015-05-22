import datetime
from dateutil import relativedelta
from mongoengine import connection

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from egauge.models import SourceReadingMonth
from system.models import System


class progressSoFarThisYear(APIView):
    def get(self, request, *args, **kwargs):
        syscode = self.kwargs['system_code']
        sys = System.objects.get(code=syscode)
        # source_ids = [str(source.id) for source in sys.sources]
        source_ids = [s.id for s in sys.sources]

        # using system timezone
        today = datetime.datetime.now(sys.time_zone)
        # from this year 1-Jan to current month usage
        this_year_first_date = datetime.datetime(
            today.year,
            1, 1, tzinfo=sys.time_zone
        )

        this_year_this_month_date = datetime.datetime(
            today.year,
            today.month, 1, tzinfo=sys.time_zone
        )

        # readings = SourceReadingMonth.objects(
        #     source_id__in=source_ids,
        #     datetime__gte=this_year_first_date,
        #     datetime__lt=this_year_this_month_date + relativedelta.relativedelta(days=1))

        mdb_conn = connection.get_db()
        measure_sum = mdb_conn.source_reading_month.aggregate([
            {'$match': {
                'source_id': {'$in': source_ids},
                'datetime': {
                    '$gte': this_year_first_date,
                    '$lt': this_year_this_month_date + relativedelta.relativedelta(days=1)
                }
            }},
            {'$group': {
                '_id': None,
                'kwh': {'$sum': '$value'}
            }}
        ])

        this_year_kwh = measure_sum['result'][0]['kwh']

        info = {'thisYearKwh': this_year_kwh}
        response = Response(info, status=status.HTTP_200_OK)
        return response


