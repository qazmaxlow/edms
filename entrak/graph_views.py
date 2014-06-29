import treelib
import decimal
import pytz
import operator
import json
import itertools
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from system.models import System
from egauge.manager import SourceManager
from egauge.models import Source
from unit.models import UnitCategory, Unit, KWH_CATEGORY_ID
from utils.utils import Utils
from user.models import EntrakUser
from utils.auth import permission_required
from utils.calculation import transform_reading, sum_all_readings

@permission_required
def graph_view(request, system_code=None):
	path = ',%s,'%system_code
	systems = System.objects.filter(Q(code=system_code) | Q(path__contains=path)).order_by('path')

	user_system_path = ',%s,'%request.user.system.code
	user_systems = System.objects.filter(Q(code=request.user.system.code) | Q(path__contains=user_system_path)).order_by('path')
	system_path_components = [code for code in systems[0].path.split(',') if code !='']
	system_path_components.append(systems[0].code)
	# TODO: trim out path that not under user system

	sources = SourceManager.get_sources(system_code, systems[0].path)

	unit_categorys = list(UnitCategory.objects.all().order_by('order'))
	# add kWh as the first unit category
	unit_categorys.insert(0, UnitCategory.getKwhCategory())

	info = {'systems': systems, 'user_systems': user_systems,
		'system_path_components': system_path_components, 'sources': sources, 'unit_categorys': unit_categorys}
	return render_to_response('graph.html', info)

@csrf_exempt
def source_readings_view(request, system_code):
	grouped_source_infos = json.loads(request.POST.get('grouped_source_infos'))
	range_type = request.POST.get('range_type')
	unit_category_id = int(request.POST.get('unit_category_id'))
	start_dt = Utils.utc_dt_from_utc_timestamp(int(decimal.Decimal(request.POST.get('start_dt'))))
	end_dt = Utils.utc_dt_from_utc_timestamp(int(decimal.Decimal(request.POST.get('end_dt'))))

	source_group_map = {}
	all_source_ids = []
	for group_idx, source_info in enumerate(grouped_source_infos):
		all_source_ids += source_info['source_ids']
		for source_id in source_info['source_ids']:
			source_group_map[source_id] = group_idx

	source_readings = SourceManager.get_readings(all_source_ids, range_type, start_dt, end_dt)

	if unit_category_id != KWH_CATEGORY_ID:
		sources = Source.objects(id__in=all_source_ids)
		source_infos = {}
		for source in sources:
			source_infos[str(source.id)] = source

		units = Unit.objects.filter(category_id=unit_category_id)

		for source_id, readings in source_readings.items():
			for reading_timestamp, reading_val in readings.items():
				readings[reading_timestamp] = transform_reading(source_infos[source_id], reading_timestamp, reading_val, unit_category_id, units)

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
def summary_view(request, system_code):
	source_ids = json.loads(request.POST.get('source_ids'))
	range_type = request.POST.get('range_type')
	start_dt = Utils.utc_dt_from_utc_timestamp(int(decimal.Decimal(request.POST.get('start_dt'))))
	end_dt = Utils.utc_dt_from_utc_timestamp(int(decimal.Decimal(request.POST.get('end_dt'))))
	last_start_dt = Utils.utc_dt_from_utc_timestamp(int(decimal.Decimal(request.POST.get('last_start_dt'))))
	last_end_dt = Utils.utc_dt_from_utc_timestamp(int(decimal.Decimal(request.POST.get('last_end_dt'))))

	source_readings = SourceManager.get_readings(source_ids, range_type, start_dt, end_dt)
	usage = sum_all_readings(source_readings)

	last_source_readings = SourceManager.get_readings(source_ids, range_type, last_start_dt, last_end_dt)
	last_usage = sum_all_readings(last_source_readings)

	return Utils.json_response({'realtime': usage, 'last': last_usage})
