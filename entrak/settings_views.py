import datetime
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.views.decorators.csrf import ensure_csrf_cookie
from system.models import System
from egauge.manager import SourceManager
from user.models import USER_ROLE_ADMIN_LEVEL
from utils.auth import permission_required

SETTINGS_TYPE_ALERT = 'alert'

@permission_required(USER_ROLE_ADMIN_LEVEL)
@ensure_csrf_cookie
def settings_view(request, system_code=None, settings_type=SETTINGS_TYPE_ALERT):
	systems_info = System.get_systems_info(system_code, request.user.system.code)
	sources = SourceManager.get_sources(systems_info["systems"][0])

	m = systems_info
	m['sources'] = sources
	m.update(csrf(request))

	return render_to_response('settings.html', m)

@permission_required(USER_ROLE_ADMIN_LEVEL)
def set_alert_view(request, system_code=None):
	alert_id = request.POST.get('alert_id')
	alert_type = request.POST.get('alert_type')
	source_info = request.POST.get('source_info')
	compare_percent = request.POST.get('compare_percent')
	peak_threshold = request.POST.get('peak_threshold')

	# fake data as frontend not ready
	start_time = datetime.datetime.strptime('14:00', '%H:%M').time()
	end_time = datetime.datetime.strptime('16:00', '%H:%M').time()
