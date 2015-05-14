from django.conf import settings
from django.db import models

from constants.schedulers import FREQUENCIES


class AutoSendReportSchedular(models.Model):
    system = models.ForeignKey('system.System')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL)
    created_time = models.DateTimeField(auto_now_add=True)
    last_execute_time = models.DateTimeField()
    frequency = models.PositiveIntegerField()


class AutoSendReportReceiver(models.Model):
    scheduler = models.ForeignKey('AutoSendReportSchedular', related_name="receivers")
    email = models.TextField()
