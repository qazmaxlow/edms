from __future__ import absolute_import

import json
import pytz
import datetime
from celery import shared_task
from django.db.models import Q
from .models import Alert, AlertHistory, AlertContact, AlertEmail
from .models import ALERT_TYPE_CONTINUOUS, ALERT_TYPE_PERIOD_END

ALERT_EMAIL_TITLE = u'test'
ALERT_EMAIL_CONTENT = u'test body'

def __valid_alert_filter_f(utc_now):
	def filter_f(alert):
		isValid = False
		now = utc_now.astimezone(pytz.timezone(alert.system.timezone))
		if now.weekday() in alert.check_weekdays:

			if alert.type == ALERT_TYPE_CONTINUOUS:
				if alert.start_time >= alert.end_time:
					if now.time() >= alert.start_time or now.time() <= alert.end_time:
						isValid = True
				else:
					if now.time() >= alert.start_time and now.time() <= alert.end_time:
						isValid = True
			elif alert.type == ALERT_TYPE_PERIOD_END:
				if (now.time() >= alert.end_time or now.time() <= alert.start_time):
					if alert.period_end_last_check is None:
						isValid = True
					else:
						end_dt = now.replace(hour=alert.end_time.hour, minute=alert.end_time.minute)
						if now.time() < alert.end_time:
							end_dt -= datetime.timedelta(days=1)
						if alert.period_end_last_check < end_dt:
							isValid = True

		return isValid

	return filter_f

@shared_task(ignore_result=True)
def check_all_alerts():
	utc_now = pytz.utc.localize(datetime.datetime.utcnow()).replace(second=0, microsecond=0)
	alerts = Alert.objects.select_related('system__timezone').all()
	need_check_alerts = filter(__valid_alert_filter_f(utc_now), alerts)

	will_insert_historys = []
	will_send_emails = []
	for alert in need_check_alerts:
		verify_result = alert.verify(utc_now)
		if alert.type == ALERT_TYPE_PERIOD_END:
			alert.period_end_last_check = utc_now
			alert.save(update_fields=['period_end_last_check'])

		need_alert = len(verify_result['fail_components']) != 0
		alert_history = None
		need_send_alert = False
		prev_history = AlertHistory.objects.filter(alert_id=alert.id).order_by('-created')

		if need_alert:
			alert_history = AlertHistory(
				alert_id=alert.id,
				created=utc_now,
				resolved=False,
				fail_components=verify_result['fail_components'])

			if len(prev_history) == 0 or (prev_history and prev_history[0].resolved):
				need_send_alert = True
		else:
			if prev_history and (not prev_history[0].resolved):
				alert_history = AlertHistory(alert_id=alert.id, created=utc_now, resolved=True)
				need_send_alert = True

		if alert_history is not None:
			will_insert_historys.append(alert_history)

		if need_send_alert:
			to_address = AlertContact.objects.filter(alerts__id=alert.id).values_list('email', flat=True)
			if to_address:
				will_send_emails.append(AlertEmail(
					to_address=json.dumps([email.encode('utf8') for email in to_address]),
					title=ALERT_EMAIL_TITLE,
					content=ALERT_EMAIL_CONTENT
				))

	AlertHistory.objects.bulk_create(will_insert_historys)
	AlertEmail.objects.bulk_create(will_send_emails)
