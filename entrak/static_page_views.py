from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.views.decorators.csrf import ensure_csrf_cookie
from system.models import System
from utils.auth import permission_required

@permission_required()
@ensure_csrf_cookie
def disclaimer_view(request, system_code=None):
	systems_info = System.get_systems_info(system_code, request.user.system.code)
	m = systems_info
	m.update(csrf(request))

	return render_to_response('disclaimer.html', m)

@permission_required()
@ensure_csrf_cookie
def faq_view(request, system_code=None):
	systems_info = System.get_systems_info(system_code, request.user.system.code)
	m = systems_info
	m.update(csrf(request))

	return render_to_response('faq.html', m)
