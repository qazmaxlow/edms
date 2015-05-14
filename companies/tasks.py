import datetime
from dateutil.relativedelta import relativedelta

from django.core.mail import EmailMultiAlternatives
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
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

                site = Site.objects.get_current()
                url_token = UrlToken.objects.create_url_token(scheduler.created_by, expiration_days=10)
                report_token = url_token.token_key

                owner = scheduler.created_by
                url = reverse('companies.reports.popup-report.custom-dates', kwargs={ 'system_code': owner.system.code })

                user_tz = scheduler.created_by.system.time_zone
                execute_time = scheduler.last_execute_time.astimezone(user_tz)

                if scheduler.frequency == scheduler_constants.MONTHLY:
                    last_report_day = execute_time + relativedelta(day=1, days=-1)
                    first_report_day = execute_time + relativedelta(day=1, months=-1)
                    report_type = 'month'
                elif scheduler.frequency == scheduler_constants.WEEKLY:
                    last_report_day = execute_time + relativedelta(days=-1)
                    first_report_day = execute_time + relativedelta(days=-7)
                    report_type = 'week'

                report_url = 'https://%s%s?start_date=%s&end_date=%s&report_type=%s&tk=%s' % (site.domain, url, first_report_day.strftime('%Y-%m-%d'), last_report_day.strftime('%Y-%m-%d'), report_type, report_token)

                email = r.email

                ctx_dict = {
                    'site': site,
                    'report_url': report_url,
                }
                subject = 'Your En-trak report is ready'
                from_email = 'noreply-en-trak.com'

                message_txt = render_to_string('companies/report_schedule/autoreport_email.txt', ctx_dict)

                email_message = EmailMultiAlternatives(subject, message_txt, from_email, [email])
                message_html = render_to_string('companies/report_schedule/autoreport_email.html', ctx_dict)
                email_message.attach_alternative(message_html, 'text/html')
                email_message.send()

                scheduler.last_execute_time = timezone.now()
                scheduler.save()
