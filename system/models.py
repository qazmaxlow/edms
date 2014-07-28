import os
import datetime
import calendar
import csv
import pytz
from django.db import models
from entrak.settings import BASE_DIR
from django.db.models import Q

SOURCE_TZ_HK = u'Asia/Hong_Kong'
UNIT_IMG_DIR = os.path.join(BASE_DIR, 'entrak', 'static', 'images', 'unit')
CITY_ALL = 'all'
KWH_CATEGORY_CODE = 'kwh'
CO2_CATEGORY_CODE = 'co2'
MONEY_CATEGORY_CODE = 'money'

DEFAULT_NIGHT_TIME_START = 20
DEFAULT_NIGHT_TIME_END = 6

class System(models.Model):
	code = models.CharField(max_length=100, unique=True)
	name = models.CharField(max_length=200)
	name_tc = models.CharField(max_length=200, blank=True)
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

	def get_all_holidays(self, start_dt, end_dt):
		system_timezone = pytz.timezone(self.timezone)
		start_date = start_dt.astimezone(system_timezone).date()
		end_date = end_dt.astimezone(system_timezone).date()
		city_holidays = CityHoliday.objects.filter(city=self.city, date__gte=start_date, date__lt=end_date).values_list('date', flat=True)
		holidays = Holiday.objects.filter(system=self, date__gte=start_date, date__lt=end_date).values_list('date', flat=True)

		all_holidays = set(city_holidays).union(holidays)
		return [holiday.strftime("%Y-%m-%d") for holiday in all_holidays]

class SystemHomeImage(models.Model):
	image = models.ImageField(upload_to="system_home/%Y/%m")
	system = models.ForeignKey(System)

class BaselineUsage(models.Model):
	system = models.ForeignKey(System)
	start_dt = models.DateTimeField()
	end_dt = models.DateTimeField()
	usage = models.FloatField()

	@staticmethod
	def get_baselines_for_systems(system_ids):
		result = {}
		for system_id in system_ids:
			result[system_id] = []
		baselines = BaselineUsage.objects.filter(system_id__in=system_ids).order_by('start_dt')
		for baseline in baselines:
			result[baseline.system_id].append(baseline)

		return result

	@staticmethod
	def transform_to_daily_usages(baselines, tz):
		result = {}

		for baseline in baselines:
			start_dt = baseline.start_dt.astimezone(tz)
			num_of_days = (baseline.end_dt.astimezone(tz) - start_dt).days + 1
			daily_usage = baseline.usage/num_of_days
			for day_diff in xrange(num_of_days):
				target_dt = start_dt + datetime.timedelta(days=day_diff)
				if target_dt.month not in result:
					result[target_dt.month] = {'dt': target_dt, 'usages':{}}
				result[target_dt.month]['usages'][target_dt.day] = daily_usage

		for month, month_info in result.items():
			# not care about the year for month
			require_month_days = 28 if (month == 2) else calendar.monthrange(1984, month)[1]
			month_usages = month_info['usages']
			if len(month_usages) < require_month_days:
				missing_days = [day for day in xrange(1,require_month_days+1) if (day not in month_usages)]
				missing_days.sort()

				if missing_days[0] == 1:
					prev_month = 12 if (month == 1) else (month - 1)
					prev_last_day = sorted(result[prev_month]['usages'])[-1]
					prev_usage = result[prev_month]['usages'][prev_last_day]
				else:
					prev_usage = month_usages[missing_days[0]-1]

				for missing_day in missing_days:
					month_usages[missing_day] = prev_usage

		return result

	@staticmethod
	def transform_to_monthly_usages(baselines, tz):
		daily_usages = BaselineUsage.transform_to_daily_usages(baselines, tz)
		result = {}
		for month, month_info in daily_usages.items():
			total = 0
			for _, usage in month_info['usages'].items():
				total += usage

			result[month] = {'dt': month_info['dt'], 'usage': total}

		return result

class UnitCategory(models.Model):
	code = models.CharField(max_length=200)
	name = models.CharField(max_length=300)
	name_tc = models.CharField(max_length=300, blank=True)
	short_desc = models.CharField(max_length=200)
	short_desc_tc = models.CharField(max_length=200)
	order = models.PositiveSmallIntegerField(default=1)
	img_off = models.CharField(max_length=200)
	img_on = models.CharField(max_length=200)
	bg_img = models.CharField(max_length=200)
	is_suffix = models.BooleanField(default=True)
	global_rate = models.FloatField(default=1)
	has_detail_rate = models.BooleanField(default=False)
	city = models.CharField(max_length=200)

class UnitRate(models.Model):
	category_code = models.CharField(max_length=200)
	code = models.CharField(max_length=200)
	rate = models.FloatField(default=1)
	effective_date = models.DateTimeField()

class CityHoliday(models.Model):
	city = models.CharField(max_length=200)
	date = models.DateField()
	desc = models.CharField(max_length=200, blank=True)

	@staticmethod
	def insert_holidays_in_csv(city, csv_path):
		holiday_date_infos = []
		with open(csv_path, 'rb') as csv_file:
			csv_reader = csv.reader(csv_file)
			for row in csv_reader:
				holiday_date_infos.append((datetime.datetime.strptime(row[0], '%Y-%m-%d').date(), row[1]))

		duplicate_holiday_dates = CityHoliday.objects.filter(
			city=city, date__in=[info[0] for info in holiday_date_infos]
		).values_list('date', flat=True)
		need_insert_holidays = []
		for info in holiday_date_infos:
			if info[0] not in duplicate_holiday_dates:
				need_insert_holidays.append(CityHoliday(city=city, date=info[0], desc=info[1]))

		CityHoliday.objects.bulk_create(need_insert_holidays)

class Holiday(models.Model):
	system = models.ForeignKey(System)
	date = models.DateField()
	desc = models.CharField(max_length=200, blank=True)
