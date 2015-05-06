from django.db import models


class UrlToken(models.Model):
    token_key = models.CharField(max_length=40)
    url = models.URLField()
    created_time = models.DateTimeField(auto_now_add=True)
    expiration_days = models.PositiveIntegerField()
