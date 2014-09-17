import datetime
import json
import pytz
import calendar
from django.shortcuts import render_to_response
from django.core.context_processors import csrf
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.html import escapejs
from django.db.models import Q
from django.db import transaction
from system.models import System
from egauge.manager import SourceManager
from alert.models import Alert, AlertHistory, ALERT_TYPE_STILL_ON, ALERT_TYPE_SUMMARY, ALERT_TYPE_PEAK, ALERT_COMPARE_METHOD_ABOVE
from contact.models import Contact
from user.models import USER_ROLE_ADMIN_LEVEL
from utils.auth import permission_required
from utils.utils import Utils

SHOW_HISTORY_DAY_MAX = 7

@permission_required(USER_ROLE_ADMIN_LEVEL)
@ensure_csrf_cookie
def alert_settings_view(request, system_code=None):
	systems_info = System.get_systems_info(system_code, request.user.system.code)
	current_system = systems_info["systems"][0]
	sources = SourceManager.get_sources(current_system)
	contact_emails = Contact.objects.filter(system__code=system_code).values_list('email', flat=True)
	alerts = Alert.objects.filter(system_id__in=[system.id for system in systems_info["systems"]]).prefetch_related('contacts')

	system_id = current_system.id
	system_timezone = pytz.timezone(current_system.timezone)

	bound_dt = pytz.utc.localize(datetime.datetime.utcnow()) - datetime.timedelta(days=SHOW_HISTORY_DAY_MAX)
	alert_historys = AlertHistory.objects.select_related('alert').filter(
		Q(created__gte=bound_dt) | Q(resolved_datetime__gte=bound_dt),
		alert__system_id=system_id).order_by('-created')

	alert_history_infos = []
	for alert_history in alert_historys:
		info = {
			'created': calendar.timegm(alert_history.created.utctimetuple()),
			'name': alert_history.alert.source_info['name'],
			'alert_type': alert_history.alert.type,
			'diff_percent': alert_history.diff_percent,
			'check_weekdays': alert_history.alert.check_weekdays,
			'resolved': alert_history.resolved,
		}
		if alert_history.resolved:
			info['resolved_datetime'] = calendar.timegm(alert_history.resolved_datetime.utctimetuple())
		if alert_history.alert.type == ALERT_TYPE_SUMMARY:
			info['start_time_h'] = alert_history.alert.start_time.hour
			info['start_time_m'] = alert_history.alert.start_time.minute
			info['end_time_h'] = alert_history.alert.end_time.hour
			info['end_time_m'] = alert_history.alert.end_time.minute

		alert_history_infos.append(info)

	m = systems_info
	m['sources'] = sources
	m['contact_emails'] = [email.encode('utf8') for email in contact_emails]
	m['alerts'] = alerts
	m['alert_history_infos'] = escapejs(json.dumps(alert_history_infos))
	m.update(csrf(request))

	return render_to_response('alert_settings.html', m)

@permission_required(USER_ROLE_ADMIN_LEVEL)
def set_alert_view(request, system_code=None):
	system_id = request.POST.get('system_id')
	alert_id = request.POST.get('alert_id')
	alert_type = request.POST.get('alert_type')
	source_info = json.loads(request.POST.get('source_info'))
	compare_percent = request.POST.get('compare_percent')
	contact_emails = json.loads(request.POST.get('contact_emails'))

	if alert_type == ALERT_TYPE_PEAK:
		peak_threshold = request.POST.get('peak_threshold')
	elif alert_type == ALERT_TYPE_SUMMARY or alert_type == ALERT_TYPE_STILL_ON:
		start_time = datetime.datetime.strptime(request.POST.get('start_time'), '%H:%M').time()
		end_time = datetime.datetime.strptime(request.POST.get('end_time'), '%H:%M').time()
		check_weekdays = json.loads(request.POST.get('check_weekdays'))

	exist_contact_emails = Contact.objects.filter(system_id=system_id, email__in=contact_emails).values_list('email', flat=True)
	need_add_contacts = []
	for email in contact_emails:
		if email not in exist_contact_emails:
			need_add_contacts.append(Contact(system_id=system_id, email=email))
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
	alert.compare_percent = compare_percent
	if alert_type == ALERT_TYPE_STILL_ON or alert_type == ALERT_TYPE_SUMMARY:
		alert.start_time = start_time
		alert.end_time = end_time
		alert.check_weekdays = check_weekdays
	elif alert_type == ALERT_TYPE_PEAK:
		alert.peak_threshold = peak_threshold
		alert.check_weekdays = []
	alert.save()
	alert.contacts.clear()
	alert.contacts.add(*contact_ids)

	return Utils.json_response({'success': True, 'alert': alert.to_info()})

@permission_required(USER_ROLE_ADMIN_LEVEL)
def remove_alert_view(request, system_code=None):
	alert_id = request.POST.get('alert_id')

	with transaction.atomic():
		AlertHistory.objects.filter(alert_id=alert_id).delete()
		Alert.objects.filter(id=alert_id).delete()
		
	return Utils.json_response({'success': True})
