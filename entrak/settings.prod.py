import os
from mongoengine import connect
from mongoengine import register_connection
from settings_common import *

DEBUG = False
ALLOWED_HOSTS = ['.en-trak.com']

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
#register_connection('entrakv4', name='entrakv4', host='ec2-54-169-90-169.ap-southeast-1.compute.amazonaws.com', tz_aware=True)

MEDIA_URL = '/media/'
LOGGING['handlers']['timed_rotating_handler']['filename'] = os.path.join('/mnt', 'logs', 'entrak', 'django_error.log')
LOGGING['handlers']['recap_timed_rotating_handler']['filename'] = os.path.join('/mnt', 'logs', 'entrak', 'django_recap.log')

SITE_LINK_FORMAT = 'https://data.en-trak.com'

PYTHON_BIN = '/app/ENV/entrak/bin/python'

ANALYTICS_TRACKING = True
