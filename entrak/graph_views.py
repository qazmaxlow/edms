import treelib
import decimal
import pytz
import operator
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from mongoengine import Q
from system.models import System
from egauge.manager import SourceManager
from unit.models import Unit
from utils.utils import Utils

def graph_view(request, system_code=None):
	path = ',%s,'%system_code
	systems = System.objects(Q(code=system_code) | Q(path__contains=path)).order_by('path')
	sources = SourceManager.get_sources(system_code, systems[0].path)
	unit_qs = []
	for source in sources:
		for category, cat_id in source.units.items():
			unit_qs.append(Q(category=category, cat_id=cat_id))
	units = Unit.objects(reduce(operator.or_, unit_qs))
	return render_to_response('graph.html', {'systems': systems, 'sources': sources, 'units': units})

@csrf_exempt
def source_readings_view(request, system_code):
	source_ids = request.POST.getlist('source_ids[]')
	range_type = request.POST.get('range_type')
	start_dt = Utils.utc_dt_from_utc_timestamp(int(decimal.Decimal(request.POST.get('start_dt'))))
	end_dt = Utils.utc_dt_from_utc_timestamp(int(decimal.Decimal(request.POST.get('end_dt'))))

	readings = SourceManager.get_readings(source_ids, range_type, start_dt, end_dt)

	last_start_dt, last_end_dt = Utils.get_last_dt_range(range_type, start_dt, end_dt);
	last_readings = SourceManager.get_readings(source_ids, range_type, last_start_dt, last_end_dt)

	return Utils.json_response({'readings': readings, 'last_readings':last_readings})
