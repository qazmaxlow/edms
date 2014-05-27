from mongoengine.document import Document
from mongoengine.fields import *
import datetime

class System(Document):
	code = StringField(max_length=100, unique=True)
	name = StringField(max_length=200)
	name_tc = StringField(max_length=200)
	intro = StringField(max_length=2000)
	intro_tc = StringField(max_length=2000)
	path = StringField(max_length=2000)
	logo = StringField(max_length=300)
	images = ListField(StringField(max_length=300))
	last_update = DateTimeField(default=datetime.datetime.now)
	location = GeoPointField()
	population = IntField()
	night_time = DictField()

class Holiday(Document):
	system_id = ListField(ReferenceField('System'))
	name = StringField(max_length=200)
	name_tc = StringField(max_length=200)
	date = DateTimeField()
