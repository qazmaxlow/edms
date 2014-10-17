"""
Django settings for entrak project.

For more information on this file, see
https://docs.djangoproject.com/en/1.6/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.6/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
from django.conf import global_settings
from django.utils.translation import ugettext_lazy as _

BASE_DIR = os.path.dirname(os.path.dirname(__file__))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.6/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '0p)mb=xm!yojbbt%nu8sid&3il&t&6fq=6+jxp(rcqr$+a$^c!'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []

STATIC_ROOT = os.path.join(BASE_DIR, 'entrak', 'static')
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.FileSystemFinder',
)

MEDIA_ROOT = os.path.join(BASE_DIR, 'entrak', 'media')

# Application definition

INSTALLED_APPS = (
    'grappelli',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'egauge',
    'system',
    'user',
    'baseline',
    'holiday',
    'unit',
    'contact',
    'alert',
    'printer',
    'entrak',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'entrak.middleware.timezone_middleware.TimezoneMiddleware',
)

TEMPLATE_CONTEXT_PROCESSORS = global_settings.TEMPLATE_CONTEXT_PROCESSORS + (
    'django.core.context_processors.request',
    'entrak.context_processors.analytics',
)

ROOT_URLCONF = 'entrak.urls'

WSGI_APPLICATION = 'entrak.wsgi.application'

# Internationalization
# https://docs.djangoproject.com/en/1.6/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

LANG_CODE_EN = 'en'
LANG_CODE_TC = 'zh-tw'
LANGUAGES = (
    (LANG_CODE_EN, _('English')),
    (LANG_CODE_TC, _('Traditional Chinese')),
)
LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

LOGGING = {
    'version': 1,
    'formatters': {
        'normal': {
            'format': '%(asctime)s %(message)s'
        },
    },
    'handlers': {
        'timed_rotating_handler': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'D',
            'formatter': 'normal',
        },
        'recap_timed_rotating_handler': {
            'level': 'DEBUG',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'D',
            'formatter': 'normal',
        },
    },
    'loggers': {
        'django.entrak_error': {
            'handlers': ['timed_rotating_handler'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.recap_data_log': {
            'handlers': ['recap_timed_rotating_handler'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['timed_rotating_handler'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

EMAIL_HOST = 'en-trak.com'
EMAIL_HOST_USER = 'alert@en-trak.com'
EMAIL_HOST_PASSWORD = 'entrak8888'
EMAIL_USE_TLS = True
EMAIL_PORT = 587

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.6/howto/static-files/

STATIC_URL = '/static/'

AUTH_USER_MODEL = 'user.EntrakUser'

# Grappelli
GRAPPELLI_ADMIN_TITLE = 'En-trak CMS'

ANALYTICS_TRACKING = False
