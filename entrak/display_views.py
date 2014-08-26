from django.shortcuts import render_to_response

def display_view(request, system_code=None):
	m = {}
	return render_to_response('display.html', m)
