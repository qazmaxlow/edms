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
from django.utils import translation
from entrak.settings_common import LANG_CODE_EN, LANG_CODE_TC
from django.contrib.sites.models import Site


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
        site = Site.objects.get_current()

        return "https://%s/users/%d/activate?uid=%s&ucode=%s"%(site.domain, self.id, uid, ucode)

    @property
    def reset_password_url(self):

        utc_time_now = datetime.now()
        utc_timestamp = (utc_time_now - datetime(1970,1,1)).total_seconds()

        encrypter = EntrakEncrypter(self.get_or_create_salt)
        uid = encrypter.encode(str(self.id))
        ucode = encrypter.encode(str(utc_timestamp))
        site = Site.objects.get_current()

        return "https://%s/users/%d/reset_password?uid=%s&ucode=%s"%(site.domain, self.id, uid, ucode)

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


    def validate_uid_and_ucode(self, uid, ucode, days=3):

        try:
            encrypter = EntrakEncrypter(self.get_or_create_salt)
            user_id = encrypter.decode(uid)
            utc_timestamp = encrypter.decode(ucode)
            utc_dt = datetime.fromtimestamp(float(utc_timestamp))

            return (user_id == str(self.id) and (datetime.now() - utc_dt).days < 7)

        except (TypeError, ValueError) as e:
            print(e)
            return False


    def send_activation_email(self, on_behalf_of=None):

        self.salt = self.get_or_create_salt
        self.save()

        plaintext = get_template('activation_email.txt')
        htmly     = get_template('activation_email.html')

        translation.activate(LANG_CODE_EN)

        if self.is_manager:
            title = _("invitation email manager title")
            heading = _("invitation email manager heading")
            description = _("invitation email manager description")
        elif on_behalf_of:
            title = _("invitation email user title")
            heading = _("{0} invitation email user heading").format(on_behalf_of.fullname)
            description = _("invitation email user description")

        site = Site.objects.get_current()

        d = Context({
                'domain': site.domain,
                'url': self.activation_url,
                'heading': heading,
                'description': description,
                'create_account_button': _('invitation email button')
            })

        subject, from_email, to_email = title, "info@en-trak.com", [self.email]

        text_content = plaintext.render(d)
        html_content = htmly.render(d)

        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()


    def send_password_reset_email(self):

        self.salt = self.get_or_create_salt
        self.save()

        plaintext = get_template('reset_password_email.txt')
        htmly     = get_template('reset_password_email.html')

        translation.activate(LANG_CODE_EN)

        title = _("reset password title")
        heading = _("reset password heading")
        description = _("reset password description")

        site = Site.objects.get_current()

        d = Context({
                'domain': site.domain,
                'url': self.reset_password_url,
                'heading': heading,
                'description': description,
                'button': _('reset password button')
            })

        subject, from_email, to_email = title, "info@en-trak.com", [self.email]

        text_content = plaintext.render(d)
        html_content = htmly.render(d)

        msg = EmailMultiAlternatives(subject, text_content, from_email, to_email)
        msg.attach_alternative(html_content, "text/html")
        msg.send()
