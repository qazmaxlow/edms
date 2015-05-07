import hashlib
import random

from django.conf import settings
from django.db import models


class UrlTokenManager(models.Manager):
    """
    Custom manager for the ``UrlToken`` model.
    The methods defined here provide shortcuts for token creation
    and for cleaning out expired tokens.
    """

    def create_url_token(self, user, expiration_days):
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

        return self.create(token_key=token_key, created_by=user, expiration_days=expiration_days)


class Token(models.Model):
    token_key = models.CharField(max_length=40, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL)
    created_time = models.DateTimeField(auto_now_add=True)
    expiration_days = models.PositiveIntegerField()
    extra_data =  models.TextField(null=True) # suppose using json format


class UrlToken(Token):
    class Meta:
        proxy = True

    objects = UrlTokenManager()
