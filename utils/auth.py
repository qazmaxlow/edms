from django.shortcuts import redirect
from user.models import EntrakUser
from system.models import System

def has_permission(request, user, system):
	valid_permission = False
	if user.is_staff:
		valid_permission = True
		if system.path == '':
			request.user.system = system
		else:
			root_system_code = [code for code in system.path.split(",") if code != ""][0]
			request.user.system = System.objects.get(code=root_system_code)
	elif user.system_id == system.id:
		valid_permission = True
	else:
		valid_permission = (user.system.code in system.path.split(","))

	return valid_permission

def permission_required(view_func):
	def wrapper(request, *args, **kwargs):
		system_code = kwargs['system_code']
		if request.user.is_authenticated():
			system = System.objects.get(code=system_code)
			if has_permission(request, request.user, system):
				return view_func(request, *args, **kwargs)
			else:
				request.session['login_warning_msg'] = "user don't have permission to access this system"
		else:
			request.session['login_warning_msg'] = 'login require! Please login first'

		return redirect('login', system_code=system_code)
	return wrapper
