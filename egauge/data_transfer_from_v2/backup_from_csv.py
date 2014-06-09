#!/usr/bin/python

import os
import sys
import pymongo
import csv
import datetime
import pytz

SOURCE_MAPPING = {
	# 'school1': [
	# 	{'xml_url': 'en-trak1015.d.en-trak.com', 'name': 'Classrooms Total'},
	# 	{'xml_url': 'en-trak1015.d.en-trak.com', 'name': 'Shared Facilities Total'},
	# ],
	# 'school2': [
	# 	{'xml_url': 'en-trak1005.d.en-trak.com', 'name': 'Aircon Total'},
	# 	{'xml_url': 'en-trak1005.d.en-trak.com', 'name': 'LP Total'},
	# ],
	'school7': [
		{'xml_url': 'en-trak1012.d.en-trak.com', 'name': 'Air Conditioning'},
		{'xml_url': 'en-trak1012.d.en-trak.com', 'name': 'Lights & Plugs'},
	],
	'school22': [
		{'xml_url': 'egauge4459.egaug.es', 'name': 'Aircon Total'},
		{'xml_url': 'egauge4459.egaug.es', 'name': 'Lights Plugs Total'},
	],
	'school76': [
		{'xml_url': 'en-trak1039.d.en-trak.com', 'name': 'showroom Lights'},
		{'xml_url': 'en-trak1039.d.en-trak.com', 'name': 'Showroom Sockets'},
	],
	'school8': [
		# {'xml_url': 'egauge984.egaug.es', 'name': 'Air Con'},
		{'xml_url': 'egauge984.egaug.es', 'name': 'Lights & Plugs'},
	],
	'school3': [
		{'xml_url': 'en-trak1010.d.en-trak.com', 'name': 'Blocks AB'},
		# {'xml_url': 'en-trak1010.d.en-trak.com', 'name': 'Blocks CD'},
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

client = pymongo.MongoClient()
hk_tz = pytz.timezone('Asia/Hong_Kong')
target_dir = sys.argv[1]
file_loop_generator = (dir_name for dir_name in os.listdir(target_dir) if os.path.isdir(os.path.join(target_dir, dir_name)))
for dir_name in file_loop_generator:
	print 'processing dir: ', dir_name
	source_ids = []
	if dir_name in SOURCE_MAPPING:
		for source_info in SOURCE_MAPPING[dir_name]:
			xml_url = source_info['xml_url']
			name = source_info['name']
			source_id = client.entrak.source.find_one({'xml_url': xml_url, 'name': name})['_id']
			source_ids.append(source_id)

	dir_path = os.path.join(target_dir, dir_name)
	for data_type in ['min', 'hour', 'day', 'week', 'month', 'year']:
		print 'processing data_type: ', data_type
		with open(os.path.join(dir_path, (data_type+'.txt')), 'rb') as f:
			reader = csv.reader(f)
			for row in reader:
				datetime_str = row[0]
				datetime_obj = hk_tz.localize(datetime.datetime.strptime(datetime_str ,"%Y-%m-%d %H:%M:%S"))
				if DATA_MAPPING[data_type]['verify_func'](datetime_obj):
					source_values = row[1:3]
					try:
						client.entrak[DATA_MAPPING[data_type]['collection']].insert([{
							'source_id': source_id,
							'datetime': datetime_obj,
							'value': source_values[idx]
						} for (idx, source_id) in enumerate(source_ids)], continue_on_error=True)
					except pymongo.errors.DuplicateKeyError, e:
						# do nothing
						pass
