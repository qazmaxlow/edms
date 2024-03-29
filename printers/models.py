# -*- coding: utf-8 -*-
from django.db import models
from mongoengine.document import Document
from mongoengine.fields import *

class Printer(models.Model):
    code = models.SlugField(max_length=200)
    name = models.CharField(max_length=200)
    system = models.ForeignKey('system.System', related_name='printers')
    order = models.IntegerField(default=1)

class BasePrinterReading(Document):
    meta = {
        'abstract': True,
        'indexes': [
            {'fields': [('p_id', 1), ("datetime", 1)], 'unique': True}
        ]
    }

    p_id = StringField(max_length=200)
    datetime = DateTimeField()
    total = IntField(default=0)
    duplex = IntField(default=0)
    one_side = IntField(default=0)
    color = IntField(default=0)
    b_n_w = IntField(default=0)
    papersize_a4 = IntField(default=0)
    papersize_non_a4 = IntField(default=0)


class PrinterReadingHour(BasePrinterReading):
    pass

class PrinterReadingDay(BasePrinterReading):
    pass

class PrinterReadingWeek(BasePrinterReading):
    pass

class PrinterReadingMonth(BasePrinterReading):
    pass

class PrinterReadingYear(BasePrinterReading):
    pass
