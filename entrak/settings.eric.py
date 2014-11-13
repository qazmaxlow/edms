import os
from mongoengine import connect
from settings_common import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'entrak',
        'USER': 'root',
        'PASSWORD': '99924361',
    }
}

connect('entrak', tz_aware=True)

MEDIA_URL = '/media/'
LOGGING['handlers']['timed_rotating_handler']['filename'] = os.path.join(os.path.dirname(BASE_DIR), 'logs', 'entrak', 'error_log')
LOGGING['handlers']['recap_timed_rotating_handler']['filename'] = os.path.join(os.path.dirname(BASE_DIR), 'logs', 'entrak', 'recap_log')

SITE_LINK_FORMAT = 'http://192.168.1.103:8001'

# PYTHON_BIN = '/app/ENV/entrak/bin/python'
