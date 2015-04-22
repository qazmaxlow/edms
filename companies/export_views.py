import csv
import json

from django.views.generic import TemplateView, View
from django.utils.decorators import method_decorator
from django.utils import dateparse

from egauge.manager import SourceManager
from egauge.models import Source, SourceReadingYear, SourceReadingMonth, SourceReadingDay, SourceReadingHour, SourceReadingMin
from system.models import System
from utils import calculation
from utils.auth import permission_required

from entrak.export_data_views import __result_generator as result_generator
from django.http import StreamingHttpResponse


class ExportView(TemplateView):
    template_name="companies/export/index.html"

    @method_decorator(permission_required())
    def dispatch(self, request, *args, **kwargs):
        return super(ExportView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(ExportView, self).get_context_data(**kwargs)
        # context['system_code'] =
        syscode = self.kwargs['system_code']

        systems_info = System.get_systems_info(syscode, self.request.user.system.code)
        context = systems_info

        context['current_system'] = systems_info['systems'][0]
        return context


class PseudoBuffer(object):
    def write(self, value):
        return value


class DownloadView(View):
    def get(self, request, *args, **kwargs):
        start_timestamp = request.GET.get('start')
        end_timestamp = request.GET.get('end')
        unit_category_code = request.GET.get('unit')

        start_dt = dateparse.parse_datetime(start_timestamp)
        end_dt = dateparse.parse_datetime(end_timestamp)

        system_code = self.kwargs['system_code']

        systems = System.get_systems_within_root(system_code)
        system = systems[0]
        sources = SourceManager.get_sources(system)
        source_ids = [str(source.id) for source in sources]
        source_id_map = {}
        for source in sources:
            source_id_map[str(source.id)] = source
            source.system = calculation.grep_system_by_code(systems, source.system_code)
            unit_info = json.loads(source.system.unit_info)
            source.money_unit_rate_code = unit_info['money']
            source.co2_unit_rate_code = unit_info['co2']

        source_readings = SourceReadingHour.objects(
            source_id__in=source_ids,
            datetime__gte=start_dt,
            datetime__lt=end_dt
        ).order_by('datetime', 'source_id')

        money_unit_rates = None
        co2_unit_rates = None
        if unit_category_code == 'money':
            money_unit_rates = UnitRate.objects.filter(category_code='money')
        elif unit_category_code == 'co2':
            co2_unit_rates = UnitRate.objects.filter(category_code='co2')
        elif unit_category_code == 'all':
            unit_rates = UnitRate.objects.filter(Q(category_code='co2') | Q(category_code='money'))
            money_unit_rates = [unit_rate for unit_rate in unit_rates if unit_rate.category_code == MONEY_CATEGORY_CODE]
            co2_unit_rates = [unit_rate for unit_rate in unit_rates if unit_rate.category_code == CO2_CATEGORY_CODE]

        pseudo_buffer = PseudoBuffer()
        csv_writer = csv.writer(pseudo_buffer)
        result_rows = result_generator(source_readings, source_id_map,
                                         unit_category_code, money_unit_rates, co2_unit_rates, system)

        response = StreamingHttpResponse((csv_writer.writerow(row) for row in result_rows),
            content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="raw_data.csv"'

        return response
