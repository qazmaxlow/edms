import datetime

from django.core.mail import EmailMultiAlternatives
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

from celery import shared_task

from constants import schedulers as scheduler_constants
from schedulers.models import AutoSendReportSchedular
from tokens.models import UrlToken


@shared_task(ignore_result=True)
def send_report_by_schedulers():
    schedulers = AutoSendReportSchedular.objects.all()

    for scheduler in schedulers:
        last_execute_time = None

        # receiver_emails = [ r.email for r in scheduler.receivers ]
        for r in scheduler.receivers.all():
            send_mail_date = scheduler.last_execute_time
            if scheduler.frequency == scheduler_constants.WEEKLY:
                send_mail_date += datetime.timedelta(days=7)
            elif scheduler.frequency == scheduler_constants.MONTHLY:
                send_mail_date += datetime.timedelta(days=30)

            if send_mail_date < timezone.now():
                from tokens.models import UrlToken

                url_token = UrlToken.objects.create_url_token(scheduler.created_by, expiration_days=10)
                report_token = url_token.token_key
                report_url = 'http://127.0.0.1:8000/adidas/report/popup-report/?start_date=2015-04-01&end_date=2015-04-30&report_type=month&tk=%s' % report_token

                email = r.email

                ctx_dict = { 'report_url': report_url }
                subject = 'Your En-trak report is ready'
                from_email = 'noreply-en-trak.com'

                message_txt = render_to_string('companies/report_schedule/autoreport_email.txt', ctx_dict)

                email_message = EmailMultiAlternatives(subject, message_txt, from_email, [email])
                message_html = render_to_string('companies/report_schedule/autoreport_email.html', ctx_dict)
                email_message.attach_alternative(message_html, 'text/html')
                email_message.send()

                scheduler.last_execute_time = timezone.now()
                scheduler.save()
