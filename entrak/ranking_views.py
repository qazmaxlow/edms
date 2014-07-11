import json
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Q
from utils.auth import permission_required
from utils.utils import Utils
from utils import calculation
from system.models import System, UnitCategory, UnitRate, KWH_CATEGORY_CODE, CITY_ALL
from egauge.models import Source
from egauge.manager import SourceManager

RANKING_TYPE_TOTAL = 'total'
RANKING_TYPE_PER_PERSON = 'per_person'
RANKING_TYPE_PERCENT = 'percent'

@permission_required
@ensure_csrf_cookie
def ranking_view(request, system_code=None):
	systems_info = System.get_systems_info(system_code, request.user.system.code)

	sources = SourceManager.get_sources(systems_info["systems"][0])

	unit_categorys = list(UnitCategory.objects.filter(Q(city=CITY_ALL) | Q(city=systems_info["systems"][0].city)).order_by('order'))

	m = systems_info
	m.update({'sources': sources, 'unit_categorys': unit_categorys})
	m.update(csrf(request))

	return render_to_response('ranking.html', m)

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

	source_readings = SourceManager.get_readings(all_source_ids, range_type, start_dt, end_dt)

	if ranking_type == RANKING_TYPE_PERCENT:
		last_start_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('last_start_dt')))
		last_end_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('last_end_dt')))
		last_source_readings = SourceManager.get_readings(all_source_ids, range_type, last_start_dt, last_end_dt)

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
	else:
		systems = None
		sources = None

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

	elif ranking_type == RANKING_TYPE_PERCENT:
		for source_id, total in sources_sum_info.items():
			last_total = reduce(lambda prev, reading: prev+reading[1], last_source_readings[source_id].items(), 0)
			sources_sum_info[source_id] = (total-last_total)/last_total*100.0

	grouped_readings = [{'name': info['name'], 'code': info.get('code', None), 'value': 0} for info in grouped_source_infos]
	for source_id, reading_val in sources_sum_info.items():
		target_group = grouped_readings[source_group_map[source_id]]
		target_group['value'] += reading_val

	return Utils.json_response(grouped_readings)
