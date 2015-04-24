from django.db import models


class AutoSendReportSchedular(models.Model):
    system = models.ForeignKey('system.System')
    created_time = models.DateTimeField(auto_now_add=True)
    last_execute_time = models.DateTimeField(auto_now_add=True)
    frequency = models.PositiveIntegerField()


class AutoSendReportReciever(models.Model):
    scheduler = models.ForeignKey('AutoSendReportSchedular', related_name="recievers")
    email = models.TextField()
