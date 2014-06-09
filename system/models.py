from mongoengine.document import Document
from mongoengine.fields import *
from mongoengine import Q
import datetime
import treelib

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

	# @staticmethod
	# def get_system_tree(school_code):
	# 	system_tree = treelib.Tree()

	# 	path = ',%s,'%school_code
	# 	systems = System.objects(Q(code=school_code) | Q(path__contains=path)).order_by('path')

	# 	for system in systems:
	# 		if system.path == None:
	# 			system_tree.create_node(0, system.code, data=system)
	# 		else:
	# 			parent_codes = filter(None, system.path.split(','))
	# 			system_tree.create_node(len(parent_codes), system.code, data=system, parent=parent_codes[-1])

	# 	return system_tree

class Holiday(Document):
	system_id = ListField(ReferenceField('System'))
	name = StringField(max_length=200)
	name_tc = StringField(max_length=200)
	date = DateTimeField()
