from django.contrib.auth.models import AbstractUser
from django.db import models

class EntrakUser(AbstractUser):
	system = models.ForeignKey('system.System', blank=True, null=True)
