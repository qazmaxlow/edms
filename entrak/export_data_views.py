import csv
import calendar
import json
from django.http import StreamingHttpResponse
from django.db.models import Q
from system.models import System
from egauge.models import SourceReadingMin
from egauge.manager import SourceManager
from unit.models import UnitRate, CO2_CATEGORY_CODE, MONEY_CATEGORY_CODE
from utils.utils import Utils
from utils import calculation

EXPORT_UNIT_ALL = 'all'

class PseudoBuffer(object):
    def write(self, value):
        return value

def __result_generator(source_readings, source_id_map, unit_category_code, money_unit_rates, co2_unit_rates):
    csv_header = ["name", "timestamp", "kWh"]
    if unit_category_code == MONEY_CATEGORY_CODE:
        csv_header.append("money")
    elif unit_category_code == CO2_CATEGORY_CODE:
        csv_header.append("co2")
    elif unit_category_code == EXPORT_UNIT_ALL:
        csv_header += ["money", "co2"]
    yield csv_header

    for reading in source_readings:
        source = source_id_map[str(reading.source_id)]
        source_name = source.name
        timestamp = calendar.timegm(reading.datetime.utctimetuple())

        result = [source_name, timestamp, reading.value]
        if unit_category_code == MONEY_CATEGORY_CODE:
            money_val = calculation.transform_reading(source.money_unit_rate_code,
                timestamp, reading.value, money_unit_rates)
            result.append(money_val)
        elif unit_category_code == CO2_CATEGORY_CODE:
            co2_val = calculation.transform_reading(source.co2_unit_rate_code,
                timestamp, reading.value, co2_unit_rates)
            result.append(co2_val)
        elif unit_category_code == EXPORT_UNIT_ALL:
            money_val = calculation.transform_reading(source.money_unit_rate_code,
                timestamp, reading.value, money_unit_rates)
            co2_val = calculation.transform_reading(source.co2_unit_rate_code,
                timestamp, reading.value, co2_unit_rates)
            result += [money_val, co2_val]

        yield result

def export_data_view(request, system_code):
    start_timestamp = int(request.POST.get('start_timestamp'))
    end_timestamp = int(request.POST.get('end_timestamp'))
    unit_category_code = request.POST.get('unit')

    start_dt = Utils.utc_dt_from_utc_timestamp(start_timestamp)
    end_dt = Utils.utc_dt_from_utc_timestamp(end_timestamp)

    systems = System.get_systems_within_root(system_code)
    system = systems[0]
    sources = SourceManager.get_sources(system)
    source_ids = [str(source.id) for source in sources]
    source_id_map = {}
    for source in sources:
        source_id_map[str(source.id)] = source
        source.system = calculation.grep_system_by_code(systems, source.system_code)
        unit_info = json.loads(source.system.unit_info)
        source.money_unit_rate_code = unit_info[MONEY_CATEGORY_CODE]
        source.co2_unit_rate_code = unit_info[CO2_CATEGORY_CODE]

    source_readings = SourceReadingMin.objects(
        source_id__in=source_ids,
        datetime__gte=start_dt,
        datetime__lt=end_dt
    ).order_by('source_id', 'datetime')

    money_unit_rates = None
    co2_unit_rates = None
    if unit_category_code == MONEY_CATEGORY_CODE:
        money_unit_rates = UnitRate.objects.filter(category_code=MONEY_CATEGORY_CODE)
    elif unit_category_code == CO2_CATEGORY_CODE:
        co2_unit_rates = UnitRate.objects.filter(category_code=CO2_CATEGORY_CODE)
    elif unit_category_code == EXPORT_UNIT_ALL:
        unit_rates = UnitRate.objects.filter(Q(category_code=CO2_CATEGORY_CODE) | Q(category_code=MONEY_CATEGORY_CODE))
        money_unit_rates = [unit_rate for unit_rate in unit_rates if unit_rate.category_code == MONEY_CATEGORY_CODE]
        co2_unit_rates = [unit_rate for unit_rate in unit_rates if unit_rate.category_code == CO2_CATEGORY_CODE]

    pseudo_buffer = PseudoBuffer()
    csv_writer = csv.writer(pseudo_buffer)
    result_rows = __result_generator(source_readings, source_id_map,
        unit_category_code, money_unit_rates, co2_unit_rates)

    response = StreamingHttpResponse((csv_writer.writerow(row) for row in result_rows),
        content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="raw_data.csv"'

    return response
