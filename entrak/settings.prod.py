import os
from mongoengine import connect
from settings_common import *

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'entrak',
        'USER': 'entrak',
        'PASSWORD': 'entrak8888',
	'HOST': 'localhost',
    }
}

connect('entrak', username="entrak", password="entrak8888", tz_aware=True)

MEDIA_URL = '/media/'
LOGGING['handlers']['timed_rotating_handler']['filename'] = os.path.join('/mnt', 'logs', 'entrak', 'django_error.log')

SITE_LINK_FORMAT = 'https://%s.en-trak.com'
