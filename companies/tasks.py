import datetime
import json
from dateutil import relativedelta

from django.core.mail import EmailMultiAlternatives
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.contrib.sites.models import Site
from django.http import QueryDict
from django.template.loader import render_to_string
from django.utils import formats
from django.utils import timezone

from celery import shared_task

from constants import schedulers as scheduler_constants
from schedulers.models import AutoSendReportSchedular
from tokens.models import UrlToken


@shared_task(ignore_result=True)
def send_report_by_schedulers():
    schedulers = AutoSendReportSchedular.objects.filter(execute_time__lte=timezone.now())

    site = Site.objects.get_current()
    subject = 'Your En-trak report is ready'
    from_email = 'noreply-en-trak.com'

    for scheduler in schedulers:
        last_execute_time = None

        owner = scheduler.created_by
        url = reverse('companies.reports.popup-report.custom-dates', kwargs={ 'system_code': scheduler.system.code })
        # build regex to match both report page and dowload page view
        url_regex = r'^%s(download/)?$' % url
        user_tz = scheduler.system.time_zone
        execute_time = scheduler.execute_time.astimezone(user_tz)

        if scheduler.frequency == scheduler_constants.MONTHLY:
            last_report_day = execute_time + relativedelta.relativedelta(day=1, days=-1)
            first_report_day = execute_time + relativedelta.relativedelta(day=1, months=-1)
            report_type = 'month'
            report_date_text = formats.date_format(first_report_day, 'YEAR_MONTH_FORMAT')
        elif scheduler.frequency == scheduler_constants.WEEKLY:
            last_report_day = execute_time + relativedelta.relativedelta(days=-1)
            first_report_day = execute_time + relativedelta.relativedelta(days=-7)
            report_type = 'week'
            report_date_text = formats.date_format(first_report_day, 'DATE_FORMAT')

        url_params = {
            'start_date': first_report_day.strftime('%Y-%m-%d'),
            'end_date' : last_report_day.strftime('%Y-%m-%d'),
            'report_type': report_type
        }
        url_params_json = json.dumps(url_params)
        url_token = UrlToken.objects.create_url_token(scheduler.created_by, expiration_days=10, url=url_regex, url_params=url_params_json)

        # report_token = url_token.token_key
        qd = QueryDict('', mutable=True)
        qd.update(url_params)
        qd.update({'tk': url_token.token_key})

        report_url = 'https://%s%s?%s' % (site.domain, url, qd.urlencode())

        ctx_dict = {
            'system': scheduler.system,
            'domain': site.domain,
            'report_url': report_url,
            'report_date_text': report_date_text,
            'description_1': "Your energy report for",
            'description_2': "is ready for your review",
            'description_3': "This link will expire 72 hours after sending\nIf you wish to view this report after that period,\nsimply log into your En-trak system and go to the Report Page",
            'button_text': 'View Report',
        }

        message_txt = render_to_string('companies/report_schedule/autoreport_email.txt', ctx_dict)
        message_html = render_to_string('companies/report_schedule/autoreport_email.html', ctx_dict)

        for r in scheduler.receivers.all():
            email_message = EmailMultiAlternatives(subject, message_txt, from_email, [r.email])
            email_message.attach_alternative(message_html, 'text/html')
            email_message.send()

        if scheduler.frequency == scheduler_constants.MONTHLY:
            next_execute_time = execute_time + relativedelta.relativedelta(day=1, months=1)
        elif scheduler.frequency == scheduler_constants.WEEKLY:
            next_execute_time = execute_time + relativedelta.relativedelta(days=1, weekday=relativedelta.SU)

        scheduler.execute_time = next_execute_time
        scheduler.save()
