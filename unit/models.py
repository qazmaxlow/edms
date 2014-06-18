# -*- coding: utf-8 -*-
from mongoengine.document import Document
from mongoengine.fields import *

class Unit(Document):
	category = StringField(max_length=50)
	cat_name = StringField(max_length=200)
	cat_id = IntField()
	name = StringField(max_length=200)
	rate = FloatField()
	effective_date = DateTimeField()
	order = IntField(default=1)
	img_off = StringField(max_length=100)
	img_on = StringField(max_length=100)
