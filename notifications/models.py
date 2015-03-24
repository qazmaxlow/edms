import datetime

from django.db import models


class MessageManger(models.Manager):
    def published(self):
        return self.active().filter(
            pub_date_start__lte=datetime.datetime.now(),
            pub_date_end__gte=datetime.datetime.now()
        )

    def active(self):
        return self.filter(is_active=True)


class Message(models.Model):
     body = models.TextField()
     is_active = models.BooleanField()
     pub_date_start = models.DateTimeField()
     pub_date_end = models.DateTimeField()

     objects = MessageManger()
