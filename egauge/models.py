# -*- coding: utf-8 -*-
from mongoengine.document import Document
from mongoengine.fields import *

SOURCE_TZ_HK = u'Asia/Hong_Kong'

class Source(Document):
	name = StringField(max_length=200)
	group = StringField(max_length=200)
	xml_url = StringField(max_length=120)
	system_code = StringField(max_length=100)
	system_path = StringField(max_length=2000)
	order = IntField()
	tz = StringField(max_length=50, default=SOURCE_TZ_HK)

class BaseSourceReading(Document):
	meta = {
		'abstract': True,
	}

	source_id = ObjectIdField()
	datetime = DateTimeField()
	value = FloatField()

class SourceReadingMin(BaseSourceReading):
	xml_url = StringField(max_length=120)
	name = StringField(max_length=200)
	valid = BooleanField()

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
