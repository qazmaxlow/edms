from django.shortcuts import render_to_response
from system.models import System
from utils.auth import permission_required

@permission_required()
def disclaimer_view(request, system_code=None):
	systems_info = System.get_systems_info(system_code, request.user.system.code)
	m = systems_info

	return render_to_response('disclaimer.html', m)

@permission_required()
def faq_view(request, system_code=None):
	systems_info = System.get_systems_info(system_code, request.user.system.code)
	m = systems_info

	return render_to_response('faq.html', m)
