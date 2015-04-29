from django.core.mail import send_mail

from celery import shared_task

from schedulers.models import AutoSendReportSchedular


@shared_task(ignore_result=True)
def send_report_by_schedulers():
    schedulers = AutoSendReportSchedular.objects.all()

    for scheduler in schedulers:
        last_execute_time = None

        # receiver_emails = [ r.email for r in scheduler.receivers ]
        for r in scheduler.receivers.all():
            email = r.email
            send_mail(
                'auto report title',
                'auto report content',
                'noreply-en-trak.com',
                [email],
                fail_silently=False)
