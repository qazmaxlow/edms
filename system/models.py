from django.db import models
import datetime
import treelib

class System(models.Model):
	code = models.CharField(max_length=100, unique=True)
	name = models.CharField(max_length=200)
	name_tc = models.CharField(max_length=200, blank=True)
	intro = models.CharField(max_length=2000, blank=True)
	intro_tc = models.CharField(max_length=2000, blank=True)
	path = models.CharField(max_length=2000, blank=True)
	logo = models.CharField(max_length=300, blank=True)
	last_update = models.DateTimeField(auto_now=True, blank=True, null=True)
	lat = models.FloatField(default=0)
	lng = models.FloatField(default=0)
	population = models.PositiveIntegerField(default=1)
	night_time_start = models.DateTimeField(blank=True, null=True)
	night_time_end = models.DateTimeField(blank=True, null=True)

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

class SystemHomeImages(models.Model):
	image = models.ImageField(upload_to="system_home/%Y/%m")
	system = models.ForeignKey(System)

# TODO: not implement yet
# class Holiday(Document):
# 	system_id = ListField(ReferenceField('System'))
# 	name = StringField(max_length=200)
# 	name_tc = StringField(max_length=200)
# 	date = DateTimeField()
