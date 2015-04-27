# coding=UTF-8
from django.contrib.auth.models import AbstractUser
from django.db import models
from Crypto.Cipher import AES
from datetime import datetime


USER_ROLE_ADMIN_LEVEL   = 100
USER_ROLE_VIEWER_LEVEL  = 1
USER_ROLE_CHOICES = (
    (USER_ROLE_ADMIN_LEVEL, 'admin'),
    (USER_ROLE_VIEWER_LEVEL, 'viewer'),
)

ENGLISH     = 1
CHINESE     = 2

USER_LANGUAGES      = (
    (ENGLISH, u'English'),
    (CHINESE, u'繁體中文'),
)


class EntrakUser(AbstractUser):

    system = models.ForeignKey('system.System', blank=True, null=True)
    role_level = models.PositiveSmallIntegerField(max_length=20, choices=USER_ROLE_CHOICES, default=USER_ROLE_VIEWER_LEVEL)
    label = models.CharField(max_length=300, blank=True)
    department = models.CharField(max_length=100, blank=True)
    language = models.PositiveSmallIntegerField(choices=USER_LANGUAGES, default=ENGLISH)
    is_email_verified = models.BooleanField(default=False)
    is_personal_account = models.BooleanField(default=False)
    salt = models.CharField(max_length=32, blank=True)


    @property
    def fullname(self):
        return '{0.first_name} {0.last_name}'.format(self)


    @property
    def activation_url(self):
        utc_time_now = datetime.now()
        return "https://en-trak.com/users/1/activate?uid=%s&ucode=%s"%(base64.b64encode(str(self.id)), base64.b64encode(str(utc_time_now - datetime(1970,1,1)).total_seconds()))


    def validate_activation_url(self, uid, ucode):

        try:
            user_id = base64.b64decode(uid)
            utc_timestamp = base64.b64decode(ucode)
            utc_dt = datetime.fromtimestamp(utc_timestamp)

            return (user_id == u.id and (datetime.now() - utc_dt).days < 2)

        except TypeError as e:
            return False


