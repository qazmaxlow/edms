from mongoengine.document import Document
from mongoengine.fields import *

class Source(Document):
	name = StringField(max_length=200)
	group = StringField(max_length=200)
	xml_url = StringField(max_length=120)
	system_code = StringField(max_length=100)
	system_path = StringField(max_length=2000)
	order = IntField()

class BaseSourceReading(Document):
	meta = {
		'abstract': True,
	}

	source_id = ObjectIdField()
	datetime = DateTimeField()
	name = StringField(max_length=200)
	value = FloatField()

class SourceReadingMin(BaseSourceReading):
	xml_url = StringField(max_length=120)
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
