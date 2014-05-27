import os
from mongoengine import connect
from settings_common import *

connect('entrak')

LOGGING['handlers']['timed_rotating_handler']['filename'] = os.path.join(os.path.dirname(BASE_DIR), 'logs', 'entrak', 'error_log')
