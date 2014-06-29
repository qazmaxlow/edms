# -*- coding: utf-8 -*-
import os
from entrak.settings import BASE_DIR
from django.db import models

UNIT_IMG_DIR = os.path.join(BASE_DIR, 'entrak', 'static', 'images', 'unit')
KWH_CATEGORY_ID = -1

class UnitCategory(models.Model):
	name = models.CharField(max_length=300)
	name_tc = models.CharField(max_length=300, blank=True)
	order = models.PositiveSmallIntegerField(default=1)
	img_off = models.CharField(max_length=200)
	img_on = models.CharField(max_length=200)
	bg_img = models.CharField(max_length=200)

	@staticmethod
	def getKwhCategory():
		return UnitCategory(id=KWH_CATEGORY_ID, name='kWh', order=0, img_off='kwh.png', img_on='kwh-hover.png', bg_img='burger-bg.png')

class Unit(models.Model):
	category = models.ForeignKey(UnitCategory)
	code = models.CharField(max_length=300)
	rate = models.FloatField(default=1)
	effective_date = models.DateTimeField()
	default = models.BooleanField(default=False)
