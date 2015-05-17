# coding=UTF-8
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models
from Crypto.Cipher import AES
from datetime import datetime
from entrak.encrypter import EntrakEncrypter

# For sending email with template
from django.core.mail import send_mail
from django.template.loader import get_template
from django.template import Context
from django.core.mail import EmailMultiAlternatives
from django.utils.translation import ugettext as _
from entrak.settings_common import LANG_CODE_EN, LANG_CODE_TC


USER_ROLE_ADMIN_LEVEL   = 100
USER_ROLE_VIEWER_LEVEL  = 1
USER_ROLE_CHOICES = (
    (USER_ROLE_ADMIN_LEVEL, 'admin'),
    (USER_ROLE_VIEWER_LEVEL, 'viewer'),
)

USER_LANGUAGES      = (
    (LANG_CODE_EN, u'English'),
    (LANG_CODE_TC, u'繁體中文'),
)


class EntrakUser(AbstractUser):

    system = models.ForeignKey('system.System', blank=True, null=True)
    role_level = models.PositiveSmallIntegerField(max_length=20, choices=USER_ROLE_CHOICES, default=USER_ROLE_VIEWER_LEVEL)
    label = models.CharField(max_length=300, blank=True)
    department = models.CharField(max_length=100, blank=True)
    language = models.CharField(max_length=10, choices=USER_LANGUAGES, default=LANG_CODE_EN)
    is_email_verified = models.BooleanField(default=False)
    is_personal_account = models.BooleanField(default=False)
    salt = models.CharField(max_length=32, blank=True)


    @property
    def fullname(self):
        return '{0.first_name} {0.last_name}'.format(self)


    @property
    def activation_url(self):

        utc_time_now = datetime.now()
        utc_timestamp = (utc_time_now - datetime(1970,1,1)).total_seconds()

        encrypter = EntrakEncrypter(self.get_or_create_salt)
        uid = encrypter.encode(str(self.id))
        ucode = encrypter.encode(str(utc_timestamp))

        return "https://data.en-trak.com/users/%d/activate?uid=%s&ucode=%s"%(self.id, uid, ucode)

    @property
    def get_or_create_salt(self):
        if not self.salt or self.salt == "":
            self.salt = uuid.uuid4().hex
            self.save()
        return self.salt


    @property
    def is_manager(self):
        # TODO: switch to Django group permission checking
        return self.role_level >= USER_ROLE_ADMIN_LEVEL


    def validate_activation_url(self, uid, ucode):

        try:
            encrypter = EntrakEncrypter(self.get_or_create_salt)
            user_id = encrypter.decode(uid)
            utc_timestamp = encrypter.decode(ucode)
            utc_dt = datetime.fromtimestamp(float(utc_timestamp))

            return (user_id == str(self.id) and (datetime.now() - utc_dt).days < 2)

        except (TypeError, ValueError) as e:
            print(e)
            return False


    def send_activation_email(self, on_behalf_of=None):

        self.salt = self.get_or_create_salt
        self.save()

        plaintext = get_template('activation_email.txt')
        htmly     = get_template('activation_email.html')

        if self.is_manager:
            title = "Invitation to Create Admin Account"
            heading = "You have been invited to create an admin account\nfor your organization’s En-trak Energy Monitoring System."
            description = "With En-trak you can see when, where and how you are spending\nyour energy dollars, enabling effective energy management."
        elif on_behalf_of:
            title = "Invitation to Create User Account"
            heading = on_behalf_of.fullname
            description = "has invited you to create an account for\nyour organization’s En-trak Energy Monitoring System."

        d = Context({
                'url': self.activation_url,
                'heading': heading,
                'description': description,
            })

        subject, from_email, to_email = title, "info@en-trak.com", [self.email]

        text_content = plaintext.render(d)
        html_content = htmly.render(d)

        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()

