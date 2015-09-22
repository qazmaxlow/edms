import json
import pytz
import datetime
import smtplib
import requests
from celery import shared_task
from django.db.models import Q
from django.core.mail import send_mail
from django.db import transaction
from .models import Alert, AlertHistory, AlertEmail
from .models import ALERT_TYPE_STILL_ON, ALERT_TYPE_SUMMARY, ALERT_TYPE_PEAK, CONTINUOUS_INTERVAL_MIN
from contact.models import Contact
from entrak.settings import EMAIL_HOST_USER
from entrak.settings import ONESIGNAL
from utils.utils import Utils
from django.contrib.auth import get_user_model


def __valid_alert_filter_f(utc_now):
    def filter_f(alert):
        isValid = False
        if alert.type == ALERT_TYPE_PEAK:
            isValid = True
        else:
            now = utc_now.astimezone(pytz.timezone(alert.system.timezone))
            if now.weekday() in alert.check_weekdays:

                if alert.type == ALERT_TYPE_STILL_ON:
                    # make sure the whole time slot lay within checking period
                    now -= datetime.timedelta(minutes=CONTINUOUS_INTERVAL_MIN)
                    if alert.start_time >= alert.end_time:
                        if now.time() >= alert.start_time or now.time() <= alert.end_time:
                            isValid = True
                    else:
                        if now.time() >= alert.start_time and now.time() <= alert.end_time:
                            isValid = True
                elif alert.type == ALERT_TYPE_SUMMARY:
                    if (now.time() >= alert.end_time):
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
def invoke_check_all_alerts():
    # this wrapper function is to ensure check alert time is correct
    utc_now = pytz.utc.localize(datetime.datetime.utcnow()).replace(second=0, microsecond=0)
    # check previous time slot to ensure data is ready
    utc_now -= datetime.timedelta(minutes=CONTINUOUS_INTERVAL_MIN)
    check_all_alerts.delay(utc_now)

@shared_task(ignore_result=True)
def check_all_alerts(check_dt):
    alerts = Alert.objects.select_related('system__code', 'system__full_name', 'system__timezone').all()
    need_check_alerts = filter(__valid_alert_filter_f(check_dt), alerts)

    will_insert_historys = []
    will_send_email_info = {}
    will_send_emails = []
    for alert in need_check_alerts:
        try:
            verify_result = alert.verify(check_dt)
        except ZeroDivisionError, e:
            Utils.log_error("ZeroDivisionError for alert: %d"%alert.id)
            continue
        if alert.type == ALERT_TYPE_SUMMARY:
            alert.summary_last_check = check_dt
            alert.save(update_fields=['summary_last_check'])

        need_alert = not (verify_result['pass_verify'])
        alert_history = None
        need_send_email = False
        prev_historys = AlertHistory.objects.filter(alert_id=alert.id).order_by('-created')
        prev_history = None

        if need_alert \
            and (len(prev_historys) == 0 or (prev_historys and prev_historys[0].resolved)):
            alert_history = AlertHistory(
                alert_id=alert.id,
                created=check_dt,
                resolved=False,
                threshold_kwh=verify_result['threshold_kwh'],
                current_kwh=verify_result['current_kwh'],
                diff_percent=verify_result['diff_percent'])

            need_send_email = True
        elif (not need_alert) \
            and (prev_historys and (not prev_historys[0].resolved)):
            prev_history = prev_historys[0]
            prev_history.resolved = True
            prev_history.resolved_datetime = check_dt
            prev_history.save()

            need_send_email = True

        if alert_history is not None:
            will_insert_historys.append(alert_history)

        if need_send_email:
            recipients = alert.contacts.values_list('email', flat=True)
            for recipient_email in recipients:
                email_key = "%s|%s|%s"%(alert.system.code, recipient_email, verify_result['pass_verify'])
                if not email_key in will_send_email_info:
                    will_send_email_info[email_key] = {}
                    will_send_email_info[email_key]['system_code'] = alert.system.code
                    will_send_email_info[email_key]['system_timezone'] = alert.system.timezone
                    will_send_email_info[email_key]['title'] = alert.gen_email_title(verify_result['pass_verify'])
                    will_send_email_info[email_key]['recipient'] = recipient_email
                    will_send_email_info[email_key]['resolved'] = verify_result['pass_verify']
                    will_send_email_info[email_key]['sub_msgs'] = []

                will_send_email_info[email_key]['sub_msgs'].append(alert.gen_email_sub_msg(verify_result, prev_history))

    for email_key, info in will_send_email_info.items():
        will_send_emails.append(AlertEmail(
            recipient=info['recipient'],
            title=info['title'],
            content=Alert.gen_email_content(info, check_dt)
        ))

    AlertHistory.objects.bulk_create(will_insert_historys)
    AlertEmail.objects.bulk_create(will_send_emails)

@shared_task(ignore_result=True)
def send_alert_email():
    send_success_email_ids = []
    header = {
        "Content-Type": "application/json",
        "Authorization": "Basic %s"%ONESIGNAL['api_key'],
    }
    with transaction.atomic():
        alert_emails = AlertEmail.objects.select_for_update().all()
        for alert_email in alert_emails:
            EntrakUser = get_user_model()
            user = EntrakUser.objects.filter(email=alert_email.recipient).first()
            if user and user.device_id:
                payload = {
                    "app_id": ONESIGNAL["app_id"],
                    "isIos": user.device_type == "apple_ios",
                    "isAndroid": user.device_type == "google_android",
                    "headings": {"en": alert_email.title},
                    "contents": {"en": alert_email.content},
                    "include_player_ids": [user.device_id],
                }
                req = requests.post("https://onesignal.com/api/v1/notifications", headers=header, data=json.dumps(payload))
                print('Mobile notification sent')
                print(payload)
                print(req.__dict__)
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