from django.contrib.auth.models import AbstractUser
from django.db import models

USER_ROLE_ADMIN_LEVEL   = 100
USER_ROLE_VIEWER_LEVEL  = 1
USER_ROLE_CHOICES = (
    (USER_ROLE_ADMIN_LEVEL, 'admin'),
    (USER_ROLE_VIEWER_LEVEL, 'viewer'),
)

class EntrakUser(AbstractUser):
    system = models.ForeignKey('system.System', blank=True, null=True)
    role_level = models.PositiveSmallIntegerField(max_length=20, choices=USER_ROLE_CHOICES, default=USER_ROLE_VIEWER_LEVEL)
    label = models.CharField(max_length=300, blank=True)

    @property
    def fullname(self):
        return '{0.first_name} {0.last_name}'.format(self)
