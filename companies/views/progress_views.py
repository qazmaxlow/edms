import datetime
from dateutil import relativedelta
from mongoengine import connection


from django.utils.translation import ugettext_lazy as _

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

        if measure_sum['result']:
            this_year_kwh = measure_sum['result'][0]['kwh']
        else:
            this_year_kwh = 0

        measure_sum = mdb_conn.source_reading_month.aggregate([
            {'$match': {
                'source_id': {'$in': source_ids},
                'datetime': {
                    '$gte': this_year_first_date - relativedelta.relativedelta(years=1),
                    '$lt': this_year_this_month_date + relativedelta.relativedelta(days=1) - relativedelta.relativedelta(years=1)
                }
            }},
            {'$group': {
                '_id': None,
                'kwh': {'$sum': '$value'}
            }}
        ])

        if measure_sum['result']:
            last_year_kwh = measure_sum['result'][0]['kwh']
        else:
            last_year_kwh = 0

        if last_year_kwh:
            compare_to_last_year = (this_year_kwh - last_year_kwh) / last_year_kwh
        else:
            compare_to_last_year = None

        info = {
            'thisYearKwh': this_year_kwh,
            'lastYearKwh': last_year_kwh,
            'compared_percent': (compare_to_last_year or 0) * 100
        }
        response = Response(info, status=status.HTTP_200_OK)
        return response


from utils import calculation
from django.utils import timezone

from baseline.models import BaselineUsage
class progressCompareToBaseline(APIView):

    def get(self, request, *args, **kwargs):
        syscode = self.kwargs['system_code']
        system = System.objects.get(code=syscode)

        # first date using entrak
        start_date = system.first_record
        start_date_year = start_date.year

        end_date = timezone.now()
        # unitrates = system.get_unitrates(start_from=start_date, target_unit='money')

        # baseline, assume this is one year data
        baselines = BaselineUsage.objects.filter(system=system).order_by('start_dt')
        year_ranges = range(start_date_year, timezone.now().year+1)

        if len(baselines) < 12:
            return Response({'noBaseline': True}, status=status.HTTP_200_OK)

        # this_year_kwh =
        total_changed = 0
        total_co2_changed = 0

        system_now = timezone.now().astimezone(system.time_zone)
        # pass 12 months, last year this month 31th > kwh < this month 1st
        pass_12months_end = system_now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        pass_12months_start = pass_12months_end - relativedelta.relativedelta(years=1)

        if pass_12months_start < start_date:
            pass_12months_start = start_date

        pass_12months_kwh = system.get_total_kwh(pass_12months_start, pass_12months_end)


        baselines = BaselineUsage.objects.filter(system=system).order_by('start_dt')

        total_baseline_kwh = 0
        if baselines.exists():
            baseline_daily_usages = BaselineUsage.transform_to_daily_usages(
                baselines,
                system.time_zone)

            total_baseline_kwh = calculation.calculate_total_baseline_energy_usage(
                pass_12months_start,
                pass_12months_end,
                baseline_daily_usages
            )


        compare = float(pass_12months_kwh - total_baseline_kwh)/total_baseline_kwh

        info = {'comparedPercent': compare * 100, 'baselineYear': baselines[0].start_dt.year}
        response = Response(info, status=status.HTTP_200_OK)
        return response
