import calendar
import json

from django.core.context_processors import csrf
from django.db.models import Q
from django.shortcuts import render_to_response
from django.views.decorators.csrf import ensure_csrf_cookie

from utils.auth import permission_required
from utils.utils import Utils

from egauge.manager import SourceManager
from entrak.settings import STATIC_URL
from system.models import System, CITY_ALL
from unit.models import UnitCategory, UnitRate, KWH_CATEGORY_CODE
from utils import calculation


@permission_required()
@ensure_csrf_cookie
def graph_view(request, system_code=None):
    systems_info = System.get_systems_info(system_code, request.user.system.code)

    sources = SourceManager.get_sources(systems_info["systems"][0])

    unit_categorys = list(UnitCategory.printer_units.filter(Q(city=CITY_ALL) | Q(city=systems_info["systems"][0].city)).order_by('order'))

    m = systems_info
    m['STATIC_URL'] = STATIC_URL
    m.update({'sources': sources, 'unit_categorys': unit_categorys})
    m.update(csrf(request))

    return render_to_response('system/printers/graph.html', m)


def show_measures_view(request, system_code):
    grouped_source_infos = json.loads(request.POST.get('grouped_source_infos'))
    range_type = request.POST.get('range_type')
    unit_category_code = request.POST.get('unit_category_code')
    has_detail_rate = (request.POST.get('has_detail_rate') == 'true')
    global_rate = float(request.POST.get('global_rate'))
    start_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('start_dt')))
    end_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('end_dt')))

    source_group_map = Utils.gen_source_group_map(grouped_source_infos)
    all_source_ids = Utils.get_source_ids_from_grouped_source_info(grouped_source_infos)

    # only one printer per one system
    system = System.get_systems_within_root(system_code)[0]
    printer = system.printers.first()
    printers_response = [{'name': printer.name}]

    from printers.models import PrinterReadingHour
    printer_measures = PrinterReadingHour.objects(
        p_id = str(printer.id),
        datetime__gte=start_dt,
        datetime__lte=end_dt
    )

    printer_readings = {}
    for printer_measure in printer_measures:
        dt_key = calendar.timegm(printer_measure.datetime.utctimetuple())
        printer_readings[dt_key] = printer_measure.total

    # convert to another units
    if unit_category_code != 'paper':
        if has_detail_rate:
            systems = System.get_systems_within_root(system_code)
            sources = Source.objects(id__in=all_source_ids)
            unit_rates = UnitRate.objects.filter(category_code=unit_category_code)

            calculation.transform_source_readings(source_readings, systems, sources, unit_rates, unit_category_code)
        else:
            for timestamp, val in printer_readings.items():
                printer_readings[timestamp] *= global_rate

    printers_response[0]['readings'] = printer_readings

    return Utils.json_response(printers_response)


def show_highest_and_lowest_view(request, system_code):
    start_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('start_dt')))
    source_infos = json.loads(request.POST.get('source_infos'))
    range_type = request.POST.get('range_type')
    unit_category_code = request.POST.get('unit_category_code')
    has_detail_rate = (request.POST.get('has_detail_rate') == 'true')
    global_rate = float(request.POST.get('global_rate'))
    tz_offset = int(request.POST.get('tz_offset'))/60
    is_highest = (request.POST.get('is_highest') == "true")
    sort_order = -1 if is_highest else 1
    systems = System.get_systems_within_root(system_code)
    current_system = systems[0]

    source_readings_info = SourceManager.get_most_readings(source_infos['source_ids'],
        range_type, tz_offset,sort_order, current_system, start_dt)
    source_readings_info['name'] = source_infos['name']

    if unit_category_code != KWH_CATEGORY_CODE:
        if has_detail_rate:
            sources = Source.objects(id__in=source_infos['source_ids'])
            unit_rates = UnitRate.objects.filter(category_code=unit_category_code)

            calculation.transform_source_readings(source_readings_info['readings'], systems, sources, unit_rates, unit_category_code)
        else:
            calculation.transform_source_readings_with_global_rate(source_readings_info['readings'], global_rate)

    total_readings = {}
    for _, readings in source_readings_info['readings'].items():
        for timestamp, val in readings.items():
            if timestamp in total_readings:
                total_readings[timestamp] += val
            else:
                total_readings[timestamp] = val
    source_readings_info['readings'] = total_readings

    return Utils.json_response(source_readings_info)
