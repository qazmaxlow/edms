import os
import datetime
import pytz
import operator
from django.db import models
from entrak.settings import BASE_DIR
from django.db.models import Q
from holiday.models import CityHoliday, Holiday

SOURCE_TZ_HK = u'Asia/Hong_Kong'
UNIT_IMG_DIR = os.path.join(BASE_DIR, 'entrak', 'static', 'images', 'unit')
CITY_ALL = 'all'

DEFAULT_NIGHT_TIME_START = 20
DEFAULT_NIGHT_TIME_END = 6

class System(models.Model):
	code = models.CharField(max_length=100, unique=True)
	name = models.CharField(max_length=200)
	name_tc = models.CharField(max_length=200, blank=True)
	full_name = models.CharField(max_length=200, blank=True)
	full_name_tc = models.CharField(max_length=200, blank=True)
	intro = models.CharField(max_length=2000, blank=True)
	intro_tc = models.CharField(max_length=2000, blank=True)
	path = models.CharField(max_length=2000, blank=True)
	logo = models.ImageField(blank=True, upload_to="system_logo/%Y/%m")
	last_update = models.DateTimeField(auto_now=True, blank=True, null=True)
	lat = models.FloatField(default=0)
	lng = models.FloatField(default=0)
	city = models.CharField(max_length=200)
	timezone = models.CharField(max_length=50, default=SOURCE_TZ_HK)
	population = models.PositiveIntegerField(default=1)
	first_record = models.DateTimeField()
	night_time_start = models.TimeField(default=datetime.time(DEFAULT_NIGHT_TIME_START))
	night_time_end = models.TimeField(default=datetime.time(DEFAULT_NIGHT_TIME_END))

	unit_info = models.TextField(default='{}')

	@staticmethod
	def get_systems_within_root(code):
		path = ',%s,'%code
		systems = System.objects.filter(Q(code=code) | Q(path__contains=path)).order_by('path')

		return systems

	@staticmethod
	def get_system_path_components(path, system_code, start_from_code, user_systems):
		system_path_components = [code for code in path.split(',') if code !='']
		system_path_components.append(system_code)
		start_idx = system_path_components.index(start_from_code)

		code_name_map = {}
		for system in user_systems:
			code_name_map[system.code] = {'name': system.name, 'name_tc': system.name_tc}

		result = []
		for code in system_path_components[start_idx:]:
			result.append({
				'code': code,
				'name': code_name_map[code]['name'],
				'name_tc': code_name_map[code]['name_tc']
			})

		return result

	@staticmethod
	def get_systems_info(system_code, user_system_code):
		systems = System.get_systems_within_root(system_code)
		user_systems = System.get_systems_within_root(user_system_code)
		system_path_components = System.get_system_path_components(systems[0].path, systems[0].code, user_system_code, user_systems)

		return {'systems': systems, 'user_systems': user_systems,
			'system_path_components': system_path_components}

	@staticmethod
	def assign_source_under_system(systems, sources):
		result = {}
		for system in systems:
			match_sources = [source for source in sources if source.system_code == system.code]
			if match_sources:
				result[system] = match_sources

		return result

	def __unicode__(self):
		return "code: %s, name: %s"%(self.code, self.name)

	def get_all_holidays(self, timestamp_info):
		system_timezone = pytz.timezone(self.timezone)
		transformed_dt_ranges = []
		for name, dt_range in timestamp_info.items():
			transformed_dt_ranges.append(
				Q(date__gte=dt_range['start'].astimezone(system_timezone).date(),
					date__lt=dt_range['end'].astimezone(system_timezone).date())
			)
		date_bounds = reduce(operator.or_, transformed_dt_ranges)
		city_holidays = CityHoliday.objects.filter(date_bounds, city=self.city).values_list('date', flat=True)
		holidays = Holiday.objects.filter(date_bounds, system=self).values_list('date', flat=True)

		all_holidays = set(city_holidays).union(holidays)
		return list(all_holidays)

class SystemHomeImage(models.Model):
	image = models.ImageField(upload_to="system_home/%Y/%m")
	system = models.ForeignKey(System)
