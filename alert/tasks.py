from __future__ import absolute_import

import json
import pytz
import datetime
import smtplib
from celery import shared_task
from django.db.models import Q
from django.core.mail import send_mail
from django.db import transaction
from .models import Alert, AlertHistory, AlertEmail
from .models import ALERT_TYPE_STILL_ON, ALERT_TYPE_SUMMARY, ALERT_TYPE_PEAK
from contact.models import Contact
from entrak.settings import EMAIL_HOST_USER

def __valid_alert_filter_f(utc_now):
    def filter_f(alert):
        isValid = False
        if alert.type == ALERT_TYPE_PEAK:
            isValid = True
        else:
            now = utc_now.astimezone(pytz.timezone(alert.system.timezone))
            if now.weekday() in alert.check_weekdays:

                if alert.type == ALERT_TYPE_STILL_ON:
                    if alert.start_time >= alert.end_time:
                        if now.time() >= alert.start_time or now.time() <= alert.end_time:
                            isValid = True
                    else:
                        if now.time() >= alert.start_time and now.time() <= alert.end_time:
                            isValid = True
                elif alert.type == ALERT_TYPE_SUMMARY:
                    if (now.time() >= alert.end_time or now.time() <= alert.start_time):
                        if alert.summary_last_check is None:
                            isValid = True
                        else:
                            end_dt = now.replace(hour=alert.end_time.hour, minute=alert.end_time.minute)
                            if now.time() < alert.end_time:
                                end_dt -= datetime.timedelta(days=1)
                            if alert.summary_last_check < end_dt:
                                isValid = True

        return isValid

    return filter_f

@shared_task(ignore_result=True)
def check_all_alerts():
    utc_now = pytz.utc.localize(datetime.datetime.utcnow()).replace(second=0, microsecond=0)
    # delay 5 minutes to ensure data is ready
    utc_now -= datetime.timedelta(minutes=5)
    alerts = Alert.objects.select_related('system__code', 'system__city', 'system__timezone').all()
    need_check_alerts = filter(__valid_alert_filter_f(utc_now), alerts)

    will_insert_historys = []
    will_send_email_info = {}
    will_send_emails = []
    for alert in need_check_alerts:
        verify_result = alert.verify(utc_now)
        if alert.type == ALERT_TYPE_SUMMARY:
            alert.summary_last_check = utc_now
            alert.save(update_fields=['summary_last_check'])

        need_alert = not (verify_result['pass_verify'])
        alert_history = None
        need_send_email = False
        prev_historys = AlertHistory.objects.filter(alert_id=alert.id).order_by('-created')

        if need_alert \
            and (len(prev_historys) == 0 or (prev_historys and prev_historys[0].resolved)):
            alert_history = AlertHistory(
                alert_id=alert.id,
                created=utc_now,
                resolved=False,
                diff_percent=verify_result['diff_percent'])

            need_send_email = True
        elif (not need_alert) \
            and (prev_historys and (not prev_historys[0].resolved)):
            prev_history = prev_historys[0]
            prev_history.resolved = True
            prev_history.resolved_datetime = utc_now
            prev_history.save()

            need_send_email = True

        if alert_history is not None:
            will_insert_historys.append(alert_history)

        if need_send_email:
            recipients = alert.contacts.values_list('email', flat=True)
            for recipient_email in recipients:
                email_key = "%s|%s|%s"%(alert.system.code, alert.type, recipient_email)
                if not email_key in will_send_email_info:
                    will_send_email_info[email_key] = {}
                    will_send_email_info[email_key]['system_code'] = alert.system.code
                    will_send_email_info[email_key]['system_city'] = alert.system.city
                    will_send_email_info[email_key]['title'] = alert.gen_email_title()
                    will_send_email_info[email_key]['recipient'] = recipient_email
                    will_send_email_info[email_key]['alert_sub_msgs'] = []
                    will_send_email_info[email_key]['resolved_sub_msgs'] = []

                sub_msgs_key = 'resolved_sub_msgs' if verify_result['pass_verify'] else 'alert_sub_msgs'
                will_send_email_info[email_key][sub_msgs_key].append(alert.gen_email_sub_msg(verify_result))

    for email_key, info in will_send_email_info.items():
        will_send_emails.append(AlertEmail(
            recipient=info['recipient'],
            title=info['title'],
            content=Alert.gen_email_content(info)
        ))

    AlertHistory.objects.bulk_create(will_insert_historys)
    AlertEmail.objects.bulk_create(will_send_emails)

@shared_task(ignore_result=True)
def send_alert_email():
    send_success_email_ids = []
    with transaction.atomic():
        alert_emails = AlertEmail.objects.select_for_update().all()
        for alert_email in alert_emails:
            try:
                send_mail(
                    alert_email.title,
                    alert_email.content,
                    EMAIL_HOST_USER,
                    [alert_email.recipient],
                    fail_silently=False)
                send_success_email_ids.append(alert_email.id)
            except smtplib.SMTPException, e:
                alert_email.error = str(e)
                alert_email.save(update_fields=['error'])

    AlertEmail.objects.filter(id__in=send_success_email_ids).delete()
