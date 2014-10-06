import os
import sys
import pymongo
import csv
import datetime
import pytz
from django.core.management.base import BaseCommand, CommandError
from mongoengine import connection

SOURCE_MAPPING = {
	'school7': [
		{'xml_url': 'en-trak1012.d.en-trak.com', 'name': 'Air Conditioning'},
		{'xml_url': 'en-trak1012.d.en-trak.com', 'name': 'Lights & Plugs'},
	],
	'school32': [
		{'xml_url': 'en-trak1023.d.en-trak.com', 'name': 'New Block'},
		{'xml_url': 'en-trak1023.d.en-trak.com', 'name': 'Old Block'},
	],
	'school24': [
		{'xml_url': 'en-trak1013.d.en-trak.com', 'name': 'Total Air Con'},
		{'xml_url': 'en-trak1014.d.en-trak.com', 'name': 'Lights & Plugs'},
	],
	'school18': [
		{'xml_url': 'egauge3055.egaug.es', 'name': 'Main Block'},
		{'xml_url': 'egauge3055.egaug.es', 'name': 'New Annex Block'},
	],
	'school17': [
		{'xml_url': 'egauge3053.egaug.es', 'name': 'Air Conditioning'},
		{'xml_url': 'egauge3053.egaug.es', 'name': 'Lights & Plugs'},
	],
	'school20': [
		{'xml_url': 'egauge3060.egaug.es', 'name': 'Air Conditioning'},
		{'xml_url': 'egauge3060.egaug.es', 'name': 'Lights & Plugs'},
	],
	'school16': [
		{'xml_url': 'egauge2196.egaug.es', 'name': 'Air Conditioning'},
		{'xml_url': 'egauge2196.egaug.es', 'name': 'Lights & Plugs'},
	],
	'school11': [
		{'xml_url': 'egauge2194.egaug.es', 'name': 'Aircon & Pool'},
		{'xml_url': 'egauge2194.egaug.es', 'name': 'Lights & Plugs'},
	],
	'school10': [
		{'xml_url': 'egauge2050.egaug.es', 'name': 'Air Conditioning'},
		{'xml_url': 'egauge2050.egaug.es', 'name': 'Lights, Plugs & Pool'},
	],
	'school8': [
		{'xml_url': 'egauge984.egaug.es', 'name': 'Air Con'},
		{'xml_url': 'egauge984.egaug.es', 'name': 'Lights & Plugs'},
	],
}

def is_min_datetime_valid(value):
	return (value.second == 0)

def is_hour_datetime_valid(value):
	return (value.second == 0 and value.minute == 0)

def is_day_datetime_valid(value):
	return (value.second == 0 and value.minute == 0 and value.hour == 0)

def is_month_datetime_valid(value):
	return (value.second == 0 and value.minute == 0 and value.hour == 0 and value.day == 1)

def is_year_datetime_valid(value):
	return (value.second == 0 and value.minute == 0 and value.hour == 0 and value.day == 1 and value.month == 1)

DATA_MAPPING = {
	'min': {'collection': 'source_reading_min', 'verify_func': is_min_datetime_valid},
	'hour': {'collection': 'source_reading_hour', 'verify_func': is_hour_datetime_valid},
	'day': {'collection': 'source_reading_day', 'verify_func': is_day_datetime_valid},
	'week': {'collection': 'source_reading_week', 'verify_func': is_day_datetime_valid},
	'month': {'collection': 'source_reading_month', 'verify_func': is_month_datetime_valid},
	'year': {'collection': 'source_reading_year', 'verify_func': is_year_datetime_valid},
}

class Command(BaseCommand):

	def handle(self, *args, **options):
		self.stdout.write('start')
		client = connection.get_db()

		hk_tz = pytz.timezone('Asia/Hong_Kong')
		target_dir = args[0]
		self.stdout.write('target root dir: '+target_dir)
		file_loop_generator = (dir_name for dir_name in os.listdir(target_dir) if os.path.isdir(os.path.join(target_dir, dir_name)))
		for dir_name in file_loop_generator:
			self.stdout.write('processing dir: '+dir_name)
			source_ids = []
			if dir_name in SOURCE_MAPPING:
				for source_info in SOURCE_MAPPING[dir_name]:
					xml_url = source_info['xml_url']
					name = source_info['name']
					source_id = client.source.find_one({'xml_url': xml_url, 'name': name})['_id']
					source_ids.append(source_id)

			dir_path = os.path.join(target_dir, dir_name)
			for data_type in ['min', 'hour', 'day', 'week', 'month', 'year']:
				self.stdout.write('processing data_type: '+data_type)
				with open(os.path.join(dir_path, (data_type+'.txt')), 'rb') as f:
					reader = csv.reader(f)
					for row in reader:
						datetime_str = row[0]
						datetime_obj = hk_tz.localize(datetime.datetime.strptime(datetime_str ,"%Y-%m-%d %H:%M:%S"))
						if DATA_MAPPING[data_type]['verify_func'](datetime_obj):
							source_values = row[1:3]
							try:
								client[DATA_MAPPING[data_type]['collection']].insert([{
									'source_id': source_id,
									'datetime': datetime_obj,
									'value': float(source_values[idx])
								} for (idx, source_id) in enumerate(source_ids)], continue_on_error=True)
							except pymongo.errors.DuplicateKeyError, e:
								# do nothing
								pass

		self.stdout.write('finish')

