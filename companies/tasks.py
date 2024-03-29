import datetime
import json
import pytz
from dateutil import relativedelta

from django.contrib.sites.models import Site
from django.core.mail import EmailMultiAlternatives
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import QueryDict
from django.template.loader import render_to_string
from django.utils import formats
from django.utils import timezone
from django.utils import translation
from django.utils.translation import ugettext as _

from celery import shared_task

from constants import schedulers as scheduler_constants
from schedulers.models import AutoSendReportSchedular
from tokens.models import UrlToken
from entrak.settings_common import LANG_CODE_EN, LANG_CODE_TC


@shared_task(ignore_result=True)
def send_report_by_schedulers():
    time_now = datetime.datetime.now(pytz.utc)
    schedulers = AutoSendReportSchedular.objects.filter(execute_time__lte=time_now)

    site = Site.objects.get_current()
    subject = 'Your En-trak report is ready'
    from_email = 'En-trak<noreply@en-trak.com>'

    for scheduler in schedulers:
        last_execute_time = None

        owner = scheduler.created_by
        system = scheduler.system
        translation.activate(owner.language)
        if system.code == 'esf' or 'esf' in system.path:
            url = reverse('companies.report_revamp.share-report.custom-dates', kwargs={ 'system_code': system.code })
        else:
            url = reverse('companies.reports.share-report.custom-dates', kwargs={ 'system_code': system.code })
        # build regex to match both report page and dowload page view
        url_regex = r'^%s(download/)?$' % url
        user_tz = system.time_zone
        execute_time = scheduler.execute_time.astimezone(user_tz)

        # skip sending report before 8:00am in user's time zone
        if time_now.astimezone(user_tz).hour < 7:
            return None

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
        url_token = UrlToken.objects.create_url_token(scheduler.created_by, expiration_days=7, url=url_regex, url_params=url_params_json)

        # report_token = url_token.token_key
        qd = QueryDict('', mutable=True)
        qd.update(url_params)
        qd.update({'tk': url_token.token_key})

        report_url = 'https://%s%s?%s' % (site.domain, url, qd.urlencode())

        if translation.get_language() == LANG_CODE_TC:
            system_name = scheduler.system.name_tc
        else:
            system_name = scheduler.system.name

        ctx_dict = {
            'domain': site.domain,
            'report_url': report_url,
            'description_1': _("automated report description 1"),
            'description_2': _("automated report description 2"),
            'system_name': system_name,
            'report_date_text': report_date_text,
            'remark': _("automated report remark"),
            'button_text': _("automated report button"),
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
