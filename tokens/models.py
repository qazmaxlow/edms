import datetime
import hashlib
import random
import re

from django.conf import settings
from django.db import models
from django.utils import timezone

SHA1_RE = re.compile('^[a-f0-9]{40}$')

class UrlTokenManager(models.Manager):
    """
    Custom manager for the ``UrlToken`` model.
    The methods defined here provide shortcuts for token creation
    and for cleaning out expired tokens.
    """

    def create_url_token(self, user, expiration_days, url, url_params=None):
        """
        Create a ``UrlToken`` for a given
        ``url`` and ``days``, and return the ``UrlToken``.
        The token key for the ``UrlToken`` will be a
        SHA1 hash, generated from a combination of the ``url``,
        days and a random salt.
        """
        salt = hashlib.sha1(str(random.random())).hexdigest()[:5]
        user_pk = str(user.pk)
        token_key = hashlib.sha1(salt+user_pk).hexdigest()

        return self.create(
            token_key=token_key,
            created_by=user,
            expiration_days=expiration_days,
            url=url,
            url_params=url_params
        )


    def check_token(self, token_key):
        """
        Validate an token key.
        If the key is valid and has not expired, return the ``User``
        If the key is not valid or has expired, return ``False``.
        """
        # Make sure the key we're trying conforms to the pattern of a
        # SHA1 hash; if it doesn't, no point trying to look it up in
        # the database.
        if SHA1_RE.search(token_key):
            try:
                token = self.get(token_key=token_key)
                return not token.is_expired
            except self.model.DoesNotExist:
                return False

        return False

    def check_token_by_request(self, request):
        token_key = request.GET.get('tk')
        if token_key:
            return self.check_token(token_key)
        else:
            return False


class AbstractToken(models.Model):
    token_key = models.CharField(max_length=40, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL)
    created_time = models.DateTimeField(auto_now_add=True)
    expiration_days = models.PositiveIntegerField()
    extra_data =  models.TextField(null=True) # suppose using json format

    class Meta:
        abstract = True

    @property
    def is_expired(self):
        expiration_date = self.created_time + datetime.timedelta(days=self.expiration_days)
        return timezone.now() > expiration_date


class UrlToken(AbstractToken):
    url = models.URLField(max_length=200)
    url_params = models.TextField(null=True) # suppose using json format

    objects = UrlTokenManager()
