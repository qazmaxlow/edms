import json
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render_to_response
from django.views.decorators.csrf import ensure_csrf_cookie
from system.models import System
from egauge.manager import SourceManager
from egauge.models import Source
from utils.utils import Utils

CAN_UPDATE_SOURCE_FIELDS = ['name', 'xml_url', 'system_code', 'system_path', 'd_name', 'd_name_tc', 'order']

def __is_source_need_update(source, info):
	need_update = False
	for compare_key in CAN_UPDATE_SOURCE_FIELDS:
		if source.__getattribute__(compare_key) != info[compare_key]:
			need_update = True
			break

	return need_update

def __assign_source_info(source, info):
	for info_key in CAN_UPDATE_SOURCE_FIELDS:
		source.__setattr__(info_key, info[info_key])

@user_passes_test(lambda user: user.is_superuser, login_url='/admin/')
@ensure_csrf_cookie
def edit_sources_view(request, system_code=None):
	if request.method == 'GET':
		systems = System.get_systems_within_root(system_code)
		sources = SourceManager.get_sources(systems[0])

		for system in systems:
			match_sources = [source for source in sources if source.system_code == system.code]
			system.sources = match_sources

		m = {}
		m['systems'] = systems

		return render_to_response('admin/edit_sources.html', m)
	elif request.method == 'POST':
		source_infos = json.loads(request.POST.get('source_infos'))
		source_ids = [info["source_id"] for info in source_infos if info["source_id"] is not None]
		sources = Source.objects(id__in=source_ids)

		source_id_map = {}
		for source in sources:
			source_id_map[str(source.id)] = source

		will_insert_sources = []
		for info in source_infos:
			if info['system_path'] == '':
				info['system_path'] = None

			try:
				info['order'] = int(info['order'])
			except ValueError, e:
				info['order'] = 1

			if info['source_id'] is None:
				will_insert_sources.append(Source(
					name=info['name'],
					xml_url=info['xml_url'],
					system_code=info['system_code'],
					system_path=info['system_path'],
					d_name=info['d_name'],
					d_name_tc=info['d_name_tc'],
					order=info['order']))
			else:
				original_source = source_id_map[info['source_id']]
				if __is_source_need_update(original_source, info):
					__assign_source_info(original_source, info)
					original_source.save()

		Source.objects.insert(will_insert_sources)

		return Utils.json_response({'success': True})
