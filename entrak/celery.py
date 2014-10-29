from __future__ import absolute_import

import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'entrak.settings')

app = Celery('entrak',
             broker='amqp://guest:entrak8888@localhost')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Optional configuration, see the application user guide.
app.conf.update(
    CELERY_TASK_RESULT_EXPIRES=10,
    CELERY_DISABLE_RATE_LIMITS=True,
    CELERY_IGNORE_RESULT=True,

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
        'retrieve-hkis-measures': {
            'task': 'egauge.tasks.retrieve_hkis_hs_reading',
            'schedule': crontab(minute='*/5'),
        },
    },

    CELERY_ROUTES = {
        'egauge.tasks.retrieve_all_reading': {'queue': 'task_starter'},
        'egauge.tasks.recover_all_invalid_reading': {'queue': 'recover'},
        'egauge.tasks.recover_min_reading_for_xml_url': {'queue': 'recover'},
        'egauge.tasks.force_retrieve_reading': {'queue': 'recap'},
        'egauge.tasks.force_retrieve_hour_reading': {'queue': 'recap'},
        'alert.tasks.invoke_check_all_alerts': {'queue': 'task_starter'},
    },
)

if __name__ == '__main__':
    app.start()
