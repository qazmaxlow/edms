from django.db import models


class Message(models.Model):
     body = models.TextField()
     is_active = models.BooleanField()
     pub_date_start = models.DateTimeField()
     pub_date_end = models.DateTimeField()
