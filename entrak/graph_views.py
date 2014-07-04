import treelib
import decimal
import pytz
import operator
import json
import itertools
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from system.models import System, UnitCategory, UnitRate, KWH_CATEGORY_ID
from egauge.manager import SourceManager
from egauge.models import Source
from utils.utils import Utils
from user.models import EntrakUser
from utils.auth import permission_required
from utils import calculation

@permission_required
def graph_view(request, system_code=None):
	systems_info = System.get_systems_info(system_code, request.user.system.code)

	sources = SourceManager.get_sources(systems_info["systems"][0])

	unit_categorys = list(UnitCategory.objects.all().order_by('order'))
	# add kWh as the first unit category
	unit_categorys.insert(0, UnitCategory.getKwhCategory())

	m = systems_info
	m.update({'sources': sources, 'unit_categorys': unit_categorys})

	return render_to_response('graph.html', m)

@csrf_exempt
def source_readings_view(request, system_code):
	grouped_source_infos = json.loads(request.POST.get('grouped_source_infos'))
	range_type = request.POST.get('range_type')
	unit_category_id = int(request.POST.get('unit_category_id'))
	start_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('start_dt')))
	end_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('end_dt')))

	source_group_map = {}
	all_source_ids = []
	for group_idx, source_info in enumerate(grouped_source_infos):
		all_source_ids += source_info['source_ids']
		for source_id in source_info['source_ids']:
			source_group_map[source_id] = group_idx

	source_readings = SourceManager.get_readings(all_source_ids, range_type, start_dt, end_dt)

	if unit_category_id != KWH_CATEGORY_ID:
		systems = System.get_systems_within_root(system_code)
		sources = Source.objects(id__in=all_source_ids)
		unit_rates = UnitRate.objects.select_related('unit').filter(unit__category_id=unit_category_id)

		calculation.transform_source_readings(source_readings, systems, sources, unit_rates, unit_category_id)

	grouped_readings = [{'name': info['name'], 'readings': {}} for info in grouped_source_infos]
	for source_id, readings in source_readings.items():
		target_group = grouped_readings[source_group_map[source_id]]['readings']
		for timestamp, val in readings.items():
			if timestamp in target_group:
				target_group[timestamp] += val
			else:
				target_group[timestamp] = val

	return Utils.json_response(grouped_readings)

@csrf_exempt
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

@csrf_exempt
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
	last_usage = sum_all_readings(last_source_readings)

	return Utils.json_response({'realtime': usage, 'last': last_usage})
