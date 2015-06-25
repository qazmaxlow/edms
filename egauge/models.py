# -*- coding: utf-8 -*-
from django.db import models

from mongoengine.document import Document
from mongoengine.document import EmbeddedDocument
from mongoengine.fields import *
from mongoengine import connection


SOURCE_TZ_HK = u'Asia/Hong_Kong'


class SourceMember(EmbeddedDocument):
    id = ObjectIdField()
    name = StringField(max_length=200)
    xml_url = StringField(max_length=120)
    tz = StringField(max_length=50, default=SOURCE_TZ_HK)
    operator = StringField(max_length=1)


class Source(Document):
    name = StringField(max_length=200)
    group = StringField(max_length=200)
    xml_url = StringField(max_length=120)
    system_code = StringField(max_length=100)
    system_path = StringField(max_length=2000)
    d_name = StringField(max_length=200)
    d_name_tc = StringField(max_length=200)
    order = IntField(default=1)
    tz = StringField(max_length=50, default=SOURCE_TZ_HK)
    source_members = ListField(EmbeddedDocumentField(SourceMember))
    active = BooleanField(default=True)


class BaseSourceReading(Document):
    meta = {
        'abstract': True,
        'indexes': [
            {'fields': [('source_id', 1), ("datetime", 1)], 'unique': True}
        ]
    }

    source_id = ObjectIdField()
    datetime = DateTimeField()
    value = FloatField()

    @classmethod
    def total_used(cls, source_ids, start_dt, end_dt):

        mdb_conn = connection.get_db()
        collection_name = cls._meta['collection']

        return getattr(mdb_conn, collection_name).aggregate([
            { "$match":
                {
                    "source_id": {"$in": source_ids},
                    "datetime": {"$gte": start_dt, "$lt": end_dt }
                }
            },
            { "$group":
                {
                    "_id": None,
                    "total": {"$sum": "$value"}
                }
            }
        ])['result']

    @classmethod
    def total_used_with_source_id(cls, source_ids, start_dt, end_dt):

        mdb_conn = connection.get_db()
        collection_name = cls._meta['collection']

        return getattr(mdb_conn, collection_name).aggregate([
            { "$match":
                {
                    "source_id": {"$in": source_ids},
                    "datetime": {"$gte": start_dt, "$lt": end_dt }
                }
            },
            { "$group":
                {
                    "_id": "$source_id",
                    "total": {"$sum": "$value"}
                }
            },
            { "$sort" :
                { "total" : -1 }
            }
        ])['result']


class SourceReadingMin(BaseSourceReading):
    pass


class SourceReadingMinInvalid(Document):
    source_id = ObjectIdField()
    datetime = DateTimeField()
    xml_url = StringField(max_length=120)
    name = StringField(max_length=200)
    tz = StringField(max_length=50, default=SOURCE_TZ_HK)


class SourceReadingHour(BaseSourceReading):
    pass


class SourceReadingDay(BaseSourceReading):
    pass


class SourceReadingWeek(BaseSourceReading):
    pass


class SourceReadingMonth(BaseSourceReading):
    pass


class SourceReadingYear(BaseSourceReading):
    pass


class StatusMonitor(models.Model):
    source_id = models.CharField(max_length=100)
    threshold = models.FloatField(null=True)

    threshold_sdt = models.TimeField(null=True)
    threshold_edt = models.TimeField(null=True)
