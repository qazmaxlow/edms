import datetime
from dateutil import relativedelta
from mongoengine import connection


from django.utils.translation import ugettext_lazy as _

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from egauge.models import SourceReadingMonth
from system.models import System


class CompareFromLastToCurrentHelper:
    def __init__(self, current_value, last_value):
        self.compared_value = float(current_value - last_value)/last_value

    @property
    def compared_percent(self):
        return self.compared_value * 100

    @property
    def compared_percent_abs(self):
        return abs(self.compared_percent) if self.compared_percent else None

    @property
    def formated_percent_change(self):
        return _('{0:.0f}% {1}').format(self.compared_percent_abs, self.change_desc) if self.compared_percent is not None else None

    @property
    def change_desc(self):
        return _('more') if self.compared_percent >=0 else _('less')

    @property
    def change_css_class(self):
        return 'more-usage' if self.compared_percent >=0 else 'less-usage'

    @property
    def text_desc(self):
        if self.compared_percent_abs:
            return _("{self.compared_percent_abs:.0f}% {self.change_desc}").format(self=self)
        else:
            return 'N/A'

    def to_dict(self):
        return {
            'percent': self.compared_percent,
            'percentAbs': self.compared_percent_abs,
            'formatedPercentChange': self.formated_percent_change,
            'desc': self.change_desc,
            'cssClass': self.change_css_class,
        }


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

        last_year_kwh = measure_sum['result'][0]['kwh']

        # compare_last_year = (this_year_kwh - last_year_kwh) / last_year_kwh

        info = {
            'thisYearKwh': this_year_kwh,
            'lastYearKwh': last_year_kwh,
            'compareToLastYearDetail': CompareFromLastToCurrentHelper(this_year_kwh, last_year_kwh).to_dict()
        }
        response = Response(info, status=status.HTTP_200_OK)
        return response


