from __future__ import absolute_import

import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'entrak.settings')

app = Celery('entrak',
             broker=settings.ENTRAK_BROKER_URL)

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Optional configuration, see the application user guide.
app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=10,
    CELERY_DISABLE_RATE_LIMITS=True,
    CELERY_IGNORE_RESULT=True,
    CELERY_TIMEZONE = 'Asia/Hong_Kong',

    CELERYBEAT_SCHEDULE = {
        'retrieve-reading-every-min': {
            'task': 'egauge.tasks.retrieve_all_reading',
            'schedule': crontab(),
        },
        'recover-reading-every-10-min': {
            'task': 'egauge.tasks.recover_all_invalid_reading',
            'schedule': crontab(minute='*/10'),
        },
        'check-alert-every-10-min': {
            'task': 'alert.tasks.invoke_check_all_alerts',
            'schedule': crontab(minute='*/10'),
        },
        'send-alert-email-every-5-min': {
            'task': 'alert.tasks.send_alert_email',
            'schedule': crontab(minute='*/5'),
        },
        'retrieve-hkis-hs-measures': {
            'task': 'egauge.tasks.retrieve_hkis_hs_measures',
            'schedule': crontab(minute='*/5'),
        },
        'retrieve-hkis-ms-measures': {
            'task': 'egauge.tasks.retrieve_hkis_ms_measures',
            'schedule': crontab(minute='*/5'),
        },
        'retrieve-hkis-ups-measures': {
            'task': 'egauge.tasks.retrieve_hkis_ups_measures',
            'schedule': crontab(minute='*/5'),
        },
        'send-report-by-schedulers': {
            'task': 'companies.tasks.send_report_by_schedulers',
            'schedule': crontab(minute='*/10'),
        },
        # 'recap-missing-readings-hourly': {
        #     'task': 'egauge.tasks.auto_recap',
        #     'schedule': crontab(minute='25'),
        #     'kwargs': {"hours": 6},
        # },
        # 'recap-missing-readings-daily': {
        #     'task': 'egauge.tasks.auto_recap',
        #     'schedule': crontab(minute='35', hour='0'),
        #     'kwargs': {"hours": 24},
        # },
    },

    CELERY_ROUTES = {
        'egauge.tasks.retrieve_all_reading': {'queue': 'task_starter'},
        'egauge.tasks.recover_all_invalid_reading': {'queue': 'task_starter'},
        'egauge.tasks.auto_recap': {'queue': 'task_starter'},
        'egauge.tasks.force_retrieve_reading': {'queue': 'task_starter'},
        'alert.tasks.invoke_check_all_alerts': {'queue': 'task_starter'},
        'egauge.tasks.recover_min_reading_for_xml_url': {'queue': 'downloader'},
        'egauge.tasks.retrieve_min_reading': {'queue': 'downloader'},
        'egauge.tasks.retrieve_source_with_members_min_reading': {'queue': 'downloader'},
        'egauge.tasks.force_retrieve_hour_reading': {'queue': 'recap'},
        'egauge.tasks.force_retrieve_source_with_members_hour_reading': {'queue': 'recap'},
        'egauge.tasks.retrieve_hkis_hs_measures': {'queue': 'recap'},
        'egauge.tasks.retrieve_hkis_ms_measures': {'queue': 'recap'},
        'egauge.tasks.retrieve_hkis_ups_measures': {'queue': 'recap'},
    },
)

if __name__ == '__main__':
    app.start()
