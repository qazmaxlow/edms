import treelib
import decimal
import pytz
import operator
from django.shortcuts import render_to_response
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from mongoengine import Q as mongoengineQ
from system.models import System
from egauge.manager import SourceManager
from unit.models import Unit
from utils.utils import Utils
from user.models import EntrakUser
from utils.auth import permission_required

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
	unit_qs = []
	for source in sources:
		for category, cat_id in source.units.items():
			unit_qs.append(mongoengineQ(category=category, cat_id=cat_id))
	units = Unit.objects(reduce(operator.or_, unit_qs))

	info = {'systems': systems, 'user_systems': user_systems,
		'system_path_components': system_path_components, 'sources': sources, 'units': units}
	return render_to_response('graph.html', info)

@csrf_exempt
def source_readings_view(request, system_code):
	source_ids = request.POST.getlist('source_ids[]')
	range_type = request.POST.get('range_type')
	start_dt = Utils.utc_dt_from_utc_timestamp(int(decimal.Decimal(request.POST.get('start_dt'))))
	end_dt = Utils.utc_dt_from_utc_timestamp(int(decimal.Decimal(request.POST.get('end_dt'))))

	result = {}
	result['readings'] = SourceManager.get_readings(source_ids, range_type, start_dt, end_dt)

	if (request.POST.get('last_start_dt') and request.POST.get('last_end_dt')):
		last_start_dt = Utils.utc_dt_from_utc_timestamp(int(decimal.Decimal(request.POST.get('last_start_dt'))))
		last_end_dt = Utils.utc_dt_from_utc_timestamp(int(decimal.Decimal(request.POST.get('last_end_dt'))))
		result['last_readings'] = SourceManager.get_readings(source_ids, range_type, last_start_dt, last_end_dt)

	return Utils.json_response(result)
