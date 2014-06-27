from user.models import EntrakUser

def permission_required(view_func):
	def wrapper(request, *args, **kwargs):
		#TODO: not implemented yet
		request.user = EntrakUser.objects.get(username="test")

		return view_func(request, *args, **kwargs)
	return wrapper
