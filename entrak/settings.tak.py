import os
from mongoengine import connect
from settings_common import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'entrak',
        'USER': 'entrak',
        'PASSWORD': 'entrak8888',
    }
}

connect('entrak')

DOMAIN_URL = "http://192.168.1.103:8001"
MEDIA_URL = '/media/'
LOGGING['handlers']['timed_rotating_handler']['filename'] = os.path.join(os.path.dirname(BASE_DIR), 'logs', 'entrak', 'error_log')
