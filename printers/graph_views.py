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


@permission_required()
@ensure_csrf_cookie
def graph_view(request, system_code=None):
    systems_info = System.get_systems_info(system_code, request.user.system.code)

    sources = SourceManager.get_sources(systems_info["systems"][0])

    unit_categorys = list(UnitCategory.objects.filter(Q(city=CITY_ALL) | Q(city=systems_info["systems"][0].city)).order_by('order'))

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

    source_readings = SourceManager.get_readings(all_source_ids, range_type, start_dt, end_dt)

    if unit_category_code != KWH_CATEGORY_CODE:
        if has_detail_rate:
            systems = System.get_systems_within_root(system_code)
            sources = Source.objects(id__in=all_source_ids)
            unit_rates = UnitRate.objects.filter(category_code=unit_category_code)

            calculation.transform_source_readings(source_readings, systems, sources, unit_rates, unit_category_code)
        else:
            calculation.transform_source_readings_with_global_rate(source_readings, global_rate)

    grouped_readings = [{'name': info['name'], 'readings': {}} for info in grouped_source_infos]
    for source_id, readings in source_readings.items():
        target_group = grouped_readings[source_group_map[source_id]]['readings']
        for timestamp, val in readings.items():
            if timestamp in target_group:
                target_group[timestamp] += val
            else:
                target_group[timestamp] = val

    return Utils.json_response(grouped_readings)
