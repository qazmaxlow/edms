import csv
import calendar
from datetime import datetime
import json
import pytz

from django.http import StreamingHttpResponse
from django.db.models import Q
from system.models import System
from egauge.models import SourceReadingHour
from egauge.manager import SourceManager
from unit.models import UnitRate, CO2_CATEGORY_CODE, MONEY_CATEGORY_CODE
from utils.utils import Utils
from utils import calculation

EXPORT_UNIT_ALL = 'all'

class PseudoBuffer(object):
    def write(self, value):
        return value

def __result_generator(source_readings, source_id_map, unit_category_code, money_unit_rates, co2_unit_rates, system=None):
    # Generate CSV header
    csv_header = ["time_stamp"]
    for reading in source_readings:
        source = source_id_map[str(reading.source_id)]
        source_name = source.name
        if not source_name in csv_header:
            csv_header.append(source_name)
        else:
            break

    yield csv_header

    last_ts = None
    source_vals = []
    for reading in source_readings:
        source = source_id_map[str(reading.source_id)]
        source_name = source.name
        timestamp = calendar.timegm(reading.datetime.utctimetuple())
        if system:
            # convert time in system's timezone
            local_tz = pytz.timezone(system.timezone)
            utc_dt = datetime.utcfromtimestamp(timestamp).replace(tzinfo=pytz.utc)
            local_dt = local_tz.normalize(utc_dt.astimezone(local_tz))
            timestamp = local_dt.strftime("%Y-%m-%d %H:%M")

        reading_val = reading.value
        if unit_category_code == MONEY_CATEGORY_CODE:
            money_val = calculation.transform_reading(source.money_unit_rate_code,
                timestamp, reading.value, money_unit_rates)
            reading_val = money_val
        elif unit_category_code == CO2_CATEGORY_CODE:
            co2_val = calculation.transform_reading(source.co2_unit_rate_code,
                timestamp, reading.value, co2_unit_rates)
            reading_val = co2_val
        # All option would not be used, remove this?
        elif unit_category_code == EXPORT_UNIT_ALL:
            money_val = calculation.transform_reading(source.money_unit_rate_code,
                timestamp, reading.value, money_unit_rates)
            co2_val = calculation.transform_reading(source.co2_unit_rate_code,
                timestamp, reading.value, co2_unit_rates)
            result += [money_val, co2_val]

        if not last_ts:
            last_ts = timestamp

        if last_ts != timestamp:
            result = [last_ts] + source_vals
            last_ts = timestamp
            source_vals = []
            yield result

        source_vals.append(reading_val)
    yield [last_ts] + source_vals

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

    source_readings = SourceReadingHour.objects(
        source_id__in=source_ids,
        datetime__gte=start_dt,
        datetime__lt=end_dt
    ).order_by('datetime', 'source_id')

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
                                     unit_category_code, money_unit_rates, co2_unit_rates, system)

    response = StreamingHttpResponse((csv_writer.writerow(row) for row in result_rows),
        content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="raw_data.csv"'

    return response
