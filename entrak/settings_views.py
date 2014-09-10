import datetime
import json
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.views.decorators.csrf import ensure_csrf_cookie
from system.models import System
from egauge.manager import SourceManager
from alert.models import Alert, ALERT_TYPE_STILL_ON, ALERT_TYPE_SUMMARY, ALERT_TYPE_PEAK, ALERT_COMPARE_METHOD_ABOVE
from contact.models import Contact
from user.models import USER_ROLE_ADMIN_LEVEL
from utils.auth import permission_required
from utils.utils import Utils

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
	system_id = request.POST.get('system_id')
	alert_id = request.POST.get('alert_id')
	alert_type = request.POST.get('alert_type')
	source_info = json.loads(request.POST.get('source_info'))
	compare_percent = request.POST.get('compare_percent')
	peak_threshold = request.POST.get('peak_threshold')

	# fake data as frontend not ready
	start_time = datetime.datetime.strptime('14:00', '%H:%M').time()
	end_time = datetime.datetime.strptime('16:00', '%H:%M').time()
	check_weekdays = json.loads('[0, 1, 2]')
	contact_info = json.loads('[{"name": "tester", "email": "tak@en-trak.com"}]')

	contact_emails = [info['email'] for info in contact_info]
	exist_contact_emails = Contact.objects.filter(system_id=system_id, email__in=contact_emails).values_list('email', flat=True)
	need_add_contacts = []
	for info in contact_info:
		if info['email'] not in exist_contact_emails:
			need_add_contacts.append(Contact(system_id=system_id, name=info['name'], email=info['email']))
	Contact.objects.bulk_create(need_add_contacts)
	contact_ids = Contact.objects.filter(system_id=system_id, email__in=contact_emails)

	if alert_id:
		alert = Alert.objects.get(id=alert_id)
	else:
		alert = Alert()

	alert.system_id = system_id
	alert.type = alert_type
	alert.source_info = source_info
	alert.compare_method = ALERT_COMPARE_METHOD_ABOVE
	if alert_type == ALERT_TYPE_STILL_ON or alert_type == ALERT_TYPE_SUMMARY:
		alert.compare_percent = compare_percent
		alert.peak_threshold = None
		alert.start_time = start_time
		alert.end_time = end_time
		alert.check_weekdays = check_weekdays
	elif alert_type == ALERT_TYPE_PEAK:
		alert.peak_threshold = peak_threshold
		alert.compare_percent = None
		alert.start_time = None
		alert.end_time = None
		alert.check_weekdays = []
	alert.save()
	alert.contacts.clear()
	alert.contacts.add(*contact_ids)

	return Utils.json_response({'success': True})
