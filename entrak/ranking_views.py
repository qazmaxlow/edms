import json
from django.shortcuts import render
from django.core.context_processors import csrf
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Q
from utils.auth import permission_required
from utils.utils import Utils
from utils import calculation
from system.models import System, CITY_ALL
from unit.models import UnitCategory, UnitRate, KWH_CATEGORY_CODE
from egauge.models import Source
from egauge.manager import SourceManager
from audit.decorators.trail import log_audit_trail
from constants import audits as constants_audits

RANKING_TYPE_TOTAL = 'total'
RANKING_TYPE_PER_PERSON = 'per_person'
RANKING_TYPE_PERCENT = 'percent'

@log_audit_trail(action_type=constants_audits.ACTION_VIEW_RANKING)
@permission_required()
@ensure_csrf_cookie
def ranking_view(request, system_code=None):
    systems_info = System.get_systems_info(system_code, request.user.system.code)

    sources = SourceManager.get_sources(systems_info["systems"][0])

    unit_categorys = list(UnitCategory.electric_units.filter(Q(city=CITY_ALL) | Q(city=systems_info["systems"][0].city)).order_by('order'))

    m = systems_info
    m.update({'sources': sources, 'unit_categorys': unit_categorys})
    m.update(csrf(request))

    return render(request, 'ranking.html', m)

def ranking_data_view(request, system_code=None):
    grouped_source_infos = json.loads(request.POST.get('grouped_source_infos'))
    range_type = request.POST.get('range_type')
    unit_category_code = request.POST.get('unit_category_code')
    has_detail_rate = (request.POST.get('has_detail_rate') == 'true')
    global_rate = float(request.POST.get('global_rate'))
    start_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('start_dt')))
    end_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('end_dt')))
    ranking_type = request.POST.get('ranking_type')

    source_group_map = Utils.gen_source_group_map(grouped_source_infos)
    all_source_ids = Utils.get_source_ids_from_grouped_source_info(grouped_source_infos)

    source_readings = SourceManager.get_readings(all_source_ids, range_type, start_dt, end_dt.replace(second=0, microsecond=0))

    if ranking_type == RANKING_TYPE_PERCENT:
        last_start_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('last_start_dt')))
        last_end_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('last_end_dt')))
        last_source_readings = SourceManager.get_readings(all_source_ids, 'hour', last_start_dt, last_end_dt.replace(second=0, microsecond=0))

    systems = None
    sources = None
    if unit_category_code != KWH_CATEGORY_CODE:
        if has_detail_rate:
            systems = System.get_systems_within_root(system_code)
            sources = Source.objects(id__in=all_source_ids)
            unit_rates = UnitRate.objects.filter(category_code=unit_category_code)

            calculation.transform_source_readings(source_readings, systems, sources, unit_rates, unit_category_code)
            if ranking_type == RANKING_TYPE_PERCENT:
                calculation.transform_source_readings(last_source_readings, systems, sources, unit_rates, unit_category_code)
        else:
            calculation.transform_source_readings_with_global_rate(source_readings, global_rate)
            if ranking_type == RANKING_TYPE_PERCENT:
                calculation.transform_source_readings_with_global_rate(last_source_readings, global_rate)

    sources_sum_info = {}
    for source_id, info in source_readings.items():
        total = reduce(lambda prev, reading: prev+reading[1], info.items(), 0)
        sources_sum_info[source_id] = total

    if ranking_type == RANKING_TYPE_PER_PERSON:
        if systems is None:
            systems = System.get_systems_within_root(system_code)
        if sources is None:
            sources = Source.objects(id__in=all_source_ids)

        system_source_mapping = calculation.gen_source_system_mapping(systems, sources)
        for source_id in sources_sum_info.keys():
            sources_sum_info[source_id] /= system_source_mapping[source_id].population

    elif ranking_type == 'per_sqfoot':
        if systems is None:
            systems = System.get_systems_within_root(system_code)
        if sources is None:
            sources = Source.objects(id__in=all_source_ids)

        system_source_mapping = calculation.gen_source_system_mapping(systems, sources)
        for source_id in sources_sum_info.keys():
            sqft = system_source_mapping[source_id].area_sqfoot or 1
            sources_sum_info[source_id] /= sqft


    grouped_readings = [{'name': info['name'], 'code': info.get('code', None), 'value': 0} for info in grouped_source_infos]
    if ranking_type == RANKING_TYPE_TOTAL or ranking_type == RANKING_TYPE_PER_PERSON or ranking_type == 'per_sqfoot':
        for source_id, reading_val in sources_sum_info.items():
            target_group = grouped_readings[source_group_map[source_id]]
            target_group['value'] += reading_val

    elif ranking_type == RANKING_TYPE_PERCENT:
        for source_id, reading_val in sources_sum_info.items():
            target_group = grouped_readings[source_group_map[source_id]]
            target_group['current'] = reading_val + target_group.get('current', 0)
            if source_id in last_source_readings:
                target_group['last'] = reduce(
                    lambda prev,reading: prev+reading[1],
                    last_source_readings[source_id].items(),
                    0) + target_group.get('last', 0)
            else:
                target_group['last'] = target_group.get('last', 0)

        for info in grouped_readings:
            if sources_sum_info and 'last' in info and info['last'] != 0:
                info['value'] = (info['current']-info['last'])/info['last']*100.0
            else:
                info['value'] = 0

    return Utils.json_response(grouped_readings)
