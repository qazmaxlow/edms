from user.models import EntrakUser
from system.models import System

def permission_required(view_func):
	def wrapper(request, *args, **kwargs):
		#TODO: not implemented yet
		system_code = kwargs['system_code']
		current_system = System.objects.get(code=system_code)
		if current_system.path:
			root_system_code = [code for code in current_system.path.split(',') if code !=''][0]
			root_system = System.objects.get(code=root_system_code)
		else:
			root_system = current_system
		request.user = EntrakUser.objects.get(system__id=root_system.id)

		return view_func(request, *args, **kwargs)
	return wrapper
