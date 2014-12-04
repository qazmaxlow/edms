from django.conf import settings
from django.db import models


class Trail(models.Model):
    action_type = models.PositiveIntegerField()
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    created_time = models.DateTimeField(auto_now_add=True)
    session_key = models.CharField(max_length=40)
    ip_address = models.IPAddressField()
    url = models.URLField()
