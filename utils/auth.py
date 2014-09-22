from functools import wraps
from django.shortcuts import redirect
from user.models import EntrakUser, USER_ROLE_ADMIN_LEVEL, USER_ROLE_VIEWER_LEVEL
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

def permission_required(required_level=USER_ROLE_VIEWER_LEVEL):
	def permission_required_decorator(view_func):
		@wraps(view_func)
		def wrapper(request, *args, **kwargs):
			system_code = kwargs['system_code']
			system = System.objects.get(code=system_code)

			if not system.login_required and required_level == USER_ROLE_VIEWER_LEVEL:
				request.user.system = system
				return view_func(request, *args, **kwargs)

			if request.user.is_authenticated():
				if request.user.role_level >= required_level and has_permission(request, request.user, system):
					return view_func(request, *args, **kwargs)
				else:
					request.session['login_warning_msg'] = "user don't have permission to access this system"
			else:
				request.session['login_warning_msg'] = 'login require! Please login first'

			return redirect('login', system_code=system_code)
		return wrapper

	return permission_required_decorator
