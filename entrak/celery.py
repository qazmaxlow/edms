from __future__ import absolute_import

import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'entrak.settings')

app = Celery('entrak',
             broker='amqp://localhost')

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
    	'recover-reading-every-hour': {
			'task': 'egauge.tasks.recover_all_invalid_reading',
			'schedule': crontab(minute=0, hour='*'),
    	},
	}
)

if __name__ == '__main__':
    app.start()
