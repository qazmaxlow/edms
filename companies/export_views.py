import csv
import calendar
import datetime
import json
import pytz

from django.views.generic import TemplateView, View
from django.utils.decorators import method_decorator
from django.utils import dateparse

from egauge.manager import SourceManager
from egauge.models import Source, SourceReadingYear, SourceReadingMonth, SourceReadingDay, SourceReadingHour, SourceReadingMin
from system.models import System
from unit.models import UnitRate
from utils import calculation
from utils.auth import permission_required

from django.http import StreamingHttpResponse


class ExportView(TemplateView):
    template_name="companies/export/index.html"

    @method_decorator(permission_required())
    def dispatch(self, request, *args, **kwargs):
        return super(ExportView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ExportView, self).get_context_data(**kwargs)
        syscode = self.kwargs['system_code']

        systems_info = System.get_systems_info(syscode, self.request.user.system.code)
        context = systems_info

        context['current_system'] = systems_info['systems'][0]
        return context


class PseudoBuffer(object):
    def write(self, value):
        return value


class DownloadView(View):

    @method_decorator(permission_required())
    def dispatch(self, request, *args, **kwargs):
        return super(DownloadView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        unit_category_code = request.GET.get('unit')
        interval = request.GET.get('interval')

        start_dt = dateparse.parse_datetime(request.GET.get('start'))
        end_dt = dateparse.parse_datetime(request.GET.get('end'))

        system_code = self.kwargs['system_code']

        systems = System.get_systems_within_root(system_code)
        system = systems.first()

        sources = system.sources
        source_ids = [str(source.id) for source in sources]

        source_id_map = {}

        for source in sources:
            source_id_map[str(source.id)] = source
            source.system = calculation.grep_system_by_code(systems, source.system_code)
            unit_info = json.loads(source.system.unit_info)
            source.money_unit_rate_code = unit_info['money']
            source.co2_unit_rate_code = unit_info['co2']

        reading_map = {
            'minute': SourceReadingMin,
            'hour': SourceReadingHour,
            'day': SourceReadingDay
        }
        reading_cls = reading_map[interval]

        source_readings = reading_cls.objects(
            source_id__in=source_ids,
            datetime__gte=start_dt,
            datetime__lt=end_dt + datetime.timedelta(days=1) # include the last date
        ).order_by('datetime', 'source_id')

        money_unit_rates = None
        co2_unit_rates = None
        if unit_category_code == 'money':
            money_unit_rates = UnitRate.objects.filter(category_code='money')
        elif unit_category_code == 'co2':
            co2_unit_rates = UnitRate.objects.filter(category_code='co2')


        pseudo_buffer = PseudoBuffer()
        csv_writer = csv.writer(pseudo_buffer)


        # Storing csv rows
        result_rows = [];

        source_headers = [s.name for s in sources]
        csv_header = ["Date Time"] + [s.d_name for s in sources]

        result_rows.append(csv_header)

        last_ts = None
        source_vals = {}
        for reading in source_readings:
            source = source_id_map[str(reading.source_id)]

            source_name = source.name
            timestamp = calendar.timegm(reading.datetime.utctimetuple())
            if system:
                # convert time in system's timezone
                utc_dt = datetime.datetime.utcfromtimestamp(timestamp).replace(tzinfo=pytz.utc)
                local_dt = utc_dt.astimezone(system.time_zone)
                timestamp = local_dt.strftime("%Y-%m-%d %H:%M")

            reading_val = reading.value
            if unit_category_code == 'money':
                money_val = calculation.transform_reading(source.money_unit_rate_code,
                    timestamp, reading.value, money_unit_rates)
                reading_val = money_val
            elif unit_category_code == 'co2':
                co2_val = calculation.transform_reading(source.co2_unit_rate_code,
                    timestamp, reading.value, co2_unit_rates)
                reading_val = co2_val

            if last_ts is None:
                last_ts = timestamp

            if last_ts != timestamp:
                result = [last_ts] + [ source_vals.get(s.name, '') for s in sources]
                result_rows.append(result)

                last_ts = timestamp
                source_vals = {}

            source_vals[source_name] = reading_val


        # Append the last row
        result = [last_ts] + [ source_vals.get(s.name, '') for s in sources]
        result_rows.append(result)

        response = StreamingHttpResponse((csv_writer.writerow(row) for row in result_rows),
            content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="raw_data.csv"'

        return response