from django.shortcuts import render_to_response
from system.models import System
from utils.auth import permission_required

SETTINGS_TYPE_ALERT = 'alert'

@permission_required
def settings_view(request, system_code=None, settings_type=SETTINGS_TYPE_ALERT):
	systems_info = System.get_systems_info(system_code, request.user.system.code)

	m = systems_info

	return render_to_response('settings.html', m)
