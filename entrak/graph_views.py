import treelib
import decimal
import pytz
import operator
import json
import itertools
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Q
from system.models import System, UnitCategory, UnitRate, CITY_ALL, KWH_CATEGORY_CODE
from egauge.manager import SourceManager
from egauge.models import Source
from utils.utils import Utils
from user.models import EntrakUser
from utils.auth import permission_required
from utils import calculation

@permission_required
@ensure_csrf_cookie
def graph_view(request, system_code=None):
	systems_info = System.get_systems_info(system_code, request.user.system.code)

	sources = SourceManager.get_sources(systems_info["systems"][0])

	unit_categorys = list(UnitCategory.objects.filter(Q(city=CITY_ALL) | Q(city=systems_info["systems"][0].city)).order_by('order'))

	m = systems_info
	m.update({'sources': sources, 'unit_categorys': unit_categorys})
	m.update(csrf(request))

	return render_to_response('graph.html', m)

def source_readings_view(request, system_code):
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

def highest_lowest_source_readings_view(request, system_code):
	source_infos = json.loads(request.POST.get('source_infos'))
	range_type = request.POST.get('range_type')
	tz_offset = int(request.POST.get('tz_offset'))/60
	is_highest = (request.POST.get('is_highest') == "true")
	sort_order = -1 if is_highest else 1

	source_readings_info = SourceManager.get_most_readings(source_infos['source_ids'], range_type, tz_offset, sort_order)
	source_readings_info['name'] = source_infos['name']

	total_readings = {}
	for _, readings in source_readings_info['readings'].items():
		for timestamp, val in readings.items():
			if timestamp in total_readings:
				total_readings[timestamp] += val
			else:
				total_readings[timestamp] = val
	source_readings_info['readings'] = total_readings

	return Utils.json_response(source_readings_info)

def summary_view(request, system_code):
	source_ids = json.loads(request.POST.get('source_ids'))
	range_type = request.POST.get('range_type')
	start_dt = Utils.utc_dt_from_utc_timestamp(int(decimal.Decimal(request.POST.get('start_dt'))))
	end_dt = Utils.utc_dt_from_utc_timestamp(int(decimal.Decimal(request.POST.get('end_dt'))))
	last_start_dt = Utils.utc_dt_from_utc_timestamp(int(decimal.Decimal(request.POST.get('last_start_dt'))))
	last_end_dt = Utils.utc_dt_from_utc_timestamp(int(decimal.Decimal(request.POST.get('last_end_dt'))))

	source_readings = SourceManager.get_readings(source_ids, range_type, start_dt, end_dt)
	usage = calculation.sum_all_readings(source_readings)

	last_source_readings = SourceManager.get_readings(source_ids, range_type, last_start_dt, last_end_dt)
	last_usage = calculation.sum_all_readings(last_source_readings)

	return Utils.json_response({'realtime': usage, 'last': last_usage})
