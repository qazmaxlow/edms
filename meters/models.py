# -*- coding: utf-8 -*-
from mongoengine.document import Document
from mongoengine.document import EmbeddedDocument
from mongoengine.fields import *
from mongoengine import connection


class HourDetail(EmbeddedDocument):
    m00 = FloatField()
    m01 = FloatField()
    m02 = FloatField()
    m03 = FloatField()
    m04 = FloatField()
    m05 = FloatField()
    m06 = FloatField()
    m07 = FloatField()
    m08 = FloatField()
    m09 = FloatField()
    m10 = FloatField()
    m11 = FloatField()
    m12 = FloatField()
    m13 = FloatField()
    m14 = FloatField()
    m15 = FloatField()
    m16 = FloatField()
    m17 = FloatField()
    m18 = FloatField()
    m19 = FloatField()
    m20 = FloatField()
    m21 = FloatField()
    m22 = FloatField()
    m23 = FloatField()
    m24 = FloatField()
    m25 = FloatField()
    m26 = FloatField()
    m27 = FloatField()
    m28 = FloatField()
    m29 = FloatField()
    m30 = FloatField()
    m31 = FloatField()
    m32 = FloatField()
    m33 = FloatField()
    m34 = FloatField()
    m35 = FloatField()
    m36 = FloatField()
    m37 = FloatField()
    m38 = FloatField()
    m39 = FloatField()
    m40 = FloatField()
    m41 = FloatField()
    m42 = FloatField()
    m43 = FloatField()
    m44 = FloatField()
    m45 = FloatField()
    m46 = FloatField()
    m47 = FloatField()
    m48 = FloatField()
    m49 = FloatField()
    m50 = FloatField()
    m51 = FloatField()
    m52 = FloatField()
    m53 = FloatField()
    m54 = FloatField()
    m55 = FloatField()
    m56 = FloatField()
    m57 = FloatField()
    m58 = FloatField()
    m59 = FloatField()


class SystemId(EmbeddedDocument):
    sid = IntField()


class Electricity(Document):

    meta = {
        'indexes': [
            {'fields': [('system_id', 1), ('source_id', 1), ("datetime_utc", 1)], 'unique': True},
            {'fields': [('system_id', 1), ("datetime_utc", 1)]},
        ]
    }

    datetime_utc = DateTimeField()
    total = FloatField()
    overnight_date = IntField() #Date stored in YYYYMMDD numeric format
    overnight_total = FloatField()
    hour_detail = EmbeddedDocumentField(HourDetail)
    parent_systems = ListField(EmbeddedDocumentField(SystemId))
    system_id = IntField()
    source_id = ObjectIdField()
    rate_co2 = FloatField()
    rate_money = FloatField()

