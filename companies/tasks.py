import datetime

from django.core.mail import send_mail
from django.utils import timezone

from celery import shared_task

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
            # send_mail_date += datetime.timedelta(days=7)

            if send_mail_date < timezone.now():
                # from tokens.models import UrlToken
                # UrlToken.objects.create_url_token(self.request.user, expiration_days=10)

                email = r.email
                send_mail(
                    'auto report title',
                    'auto report content',
                    'noreply-en-trak.com',
                    [email],
                    fail_silently=False)
                scheduler.last_execute_time = timezone.now()
                scheduler.save()
