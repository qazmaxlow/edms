import requests
import pytz
import calendar
import time
import datetime
import logging
from bson.code import Code
from bson.objectid import ObjectId
from mongoengine import connection, Q, NotUniqueError
from .models import Source, SourceReadingMin, SourceReadingHour,\
	SourceReadingDay, SourceReadingWeek, SourceReadingMonth, SourceReadingYear, SourceReadingMinInvalid
from lxml import etree
from collections import defaultdict
from utils.utils import Utils

class SourceManager:

	DEFAULT_USERNAME = 'entrak'
	DEFAULT_PASSWORD = 'jianshu1906'
	INVALID_RECOVER_LIMIT = 2000

	class GetEgaugeDataError(Exception):
		pass

	class TimeDeltaNotMatchError(Exception):
		pass

	@staticmethod
	def get_grouped_sources(system_codes=None):
		current_db_conn = connection.get_db()
		aggregate_pipeline = [
			{ "$match": {"active": True} },
			{ "$project": {"_id": 1, "name": 1, "tz": 1, "xml_url": 1}},
			{
				"$group": {
					"_id": "$xml_url",
					"sources": {"$push": {"_id": "$_id", "name": "$name", "tz": "$tz"}}
				}
			}
		]
		if system_codes:
			aggregate_pipeline[0]["$match"]["system_code"] = {"$in": system_codes}
		result = current_db_conn.source.aggregate(aggregate_pipeline)

		return result['result']

	@staticmethod
	def gen_retrieve_time():
		retrieve_time = datetime.datetime.utcnow()
		retrieve_time = pytz.utc.localize(retrieve_time.replace(second=0, microsecond=0))
		# delay 2 minutes to ensure data at meter is ready
		retrieve_time -= datetime.timedelta(minutes=2)

		return retrieve_time

	@staticmethod
	def retrieve_all_reading():
		retrieve_time = SourceManager.gen_retrieve_time()
		for grouped_sources in SourceManager.get_grouped_sources():
			xml_url = grouped_sources['_id']
			sources = grouped_sources['sources']

			SourceManager.retrieve_min_reading(xml_url, sources, retrieve_time)

	@staticmethod
	def retrieve_min_reading(xml_url, infos, retrieve_time):
		source_reading_mins = []
		source_reading_mins_invalid = []
		need_update_source_ids = []
		start_timestamp = calendar.timegm(retrieve_time.utctimetuple())
		try:
			readings = SourceManager.__get_egauge_data(xml_url, start_timestamp, 1)
			for info in infos:
				construct_info = {
					'datetime': retrieve_time,
					'source_id': info['_id'],
				}
				if info['name'] in readings:
					construct_info['value'] = readings[info['name']][0]
					source_reading_min = SourceReadingMin(**construct_info)
					source_reading_mins.append(source_reading_min)
					need_update_source_ids.append(info['_id'])
				else:
					Utils.log_error("no matching cname for source! source: %s, cname: %s"%(xml_url, info['name']))
					construct_info['xml_url'] = xml_url
					construct_info['name'] = info['name']
					construct_info['tz'] = info['tz']
					source_reading_mins_invalid.append(SourceReadingMinInvalid(**construct_info))
		except SourceManager.GetEgaugeDataError, e:
			source_reading_mins_invalid = [SourceReadingMinInvalid(
					datetime=retrieve_time,
					source_id=info['_id'],
					name=info['name'],
					xml_url=xml_url,
					tz=info['tz']
			) for info in infos]
			Utils.log_exception(e)

		if source_reading_mins:
			SourceReadingMin.objects.insert(source_reading_mins)
		if source_reading_mins_invalid:
			SourceReadingMinInvalid.objects.insert(source_reading_mins_invalid)

		if need_update_source_ids:
			# source with same XML should be same timezone
			source_tz = infos[0]['tz']
			SourceManager.update_sum(retrieve_time, source_tz, need_update_source_ids)

	@staticmethod
	def update_sum(retrieve_time, source_tz, source_ids):
		sum_infos = [
			{'range_type': Utils.RANGE_TYPE_HOUR, 'target_collection': 'source_reading_min', 'update_class': SourceReadingHour},
			{'range_type': Utils.RANGE_TYPE_DAY, 'target_collection': 'source_reading_hour', 'update_class': SourceReadingDay},
			{'range_type': Utils.RANGE_TYPE_WEEK, 'target_collection': 'source_reading_day', 'update_class': SourceReadingWeek},
			{'range_type': Utils.RANGE_TYPE_MONTH, 'target_collection': 'source_reading_day', 'update_class': SourceReadingMonth},
			{'range_type': Utils.RANGE_TYPE_YEAR, 'target_collection': 'source_reading_month', 'update_class': SourceReadingYear},
		]

		local_retrieve_time = retrieve_time.astimezone(pytz.timezone(source_tz))
		for sum_info in sum_infos:
			start_time, end_time = Utils.get_datetime_range(sum_info['range_type'], local_retrieve_time)

			current_db_conn = connection.get_db()
			result = current_db_conn[sum_info['target_collection']].aggregate([
				{"$match": {
					'source_id': {'$in': source_ids},
					'datetime': {'$gte': start_time, '$lt': end_time}}
				},
				{"$project": {"source_id": 1, "value": 1}},
				{
					"$group": {
						"_id": "$source_id",
						"value": {"$sum": "$value"}
					}
				}
			])

			for info in result['result']:
				sum_info['update_class'].objects(
					source_id=info['_id'], datetime=start_time
				).update_one(set__value=info['value'], upsert=True)

	@staticmethod
	def get_grouped_invalid_readings(xml_url):
		current_db_conn = connection.get_db()
		result = current_db_conn['source_reading_min_invalid'].aggregate([
			{ "$match": {"xml_url": xml_url} },
			{
				"$group": {
					"_id": "$datetime",
					"sources": {"$push": {"_id": "$_id", "source_id": "$source_id", "name": "$name", "tz":"$tz"}}
				},
			},
			{"$limit": SourceManager.INVALID_RECOVER_LIMIT}
		], allowDiskUse=True)

		return result['result']

	@staticmethod
	def recover_all_invalid_reading():
		for xml_url in SourceReadingMinInvalid.objects.distinct('xml_url'):
			SourceManager.recover_min_reading_for_xml_url(xml_url)

	@staticmethod
	def recover_min_reading_for_xml_url(xml_url):
		grouped_invalid_readings = SourceManager.get_grouped_invalid_readings(xml_url)
		for grouped_invalid_reading in grouped_invalid_readings:
			try:
				SourceManager.recover_min_reading(xml_url, grouped_invalid_reading)
			except SourceManager.GetEgaugeDataError, e:
				break

	@staticmethod
	def recover_min_reading(xml_url, grouped_invalid_reading):
		retrieve_time = (grouped_invalid_reading['_id']).astimezone(pytz.utc)
		sources = grouped_invalid_reading['sources']

		start_timestamp = calendar.timegm(retrieve_time.utctimetuple())
		source_reading_mins = []
		need_update_source_ids = []
		will_remove_invalid_reading = []
		try:
			readings = SourceManager.__get_egauge_data(xml_url, start_timestamp, 1)
			for source in sources:
				if source['name'] in readings:
					source_reading_min = SourceReadingMin(
						datetime=retrieve_time,
						source_id=source['source_id'],
						value=readings[source['name']][0]
					)
					source_reading_mins.append(source_reading_min)
					need_update_source_ids.append(source['source_id'])
				else:
					Utils.log_error("non-exist cname for source at recover! source: %s, cname: %s"%(xml_url, source['name']))
				will_remove_invalid_reading.append(source['_id'])
		except SourceManager.TimeDeltaNotMatchError, e:
			# not handle compressed data when recover at this stage
			will_remove_invalid_reading = [source['_id'] for source in sources]

		if source_reading_mins:
			try:
				SourceReadingMin.objects.insert(source_reading_mins, write_concern={'continue_on_error': True})
			except NotUniqueError, e:
				# do nothing
				pass
		if need_update_source_ids:
			source_tz = sources[0]['tz']
			SourceManager.update_sum(retrieve_time, source_tz, need_update_source_ids)
		if will_remove_invalid_reading:
			SourceReadingMinInvalid.objects(id__in=will_remove_invalid_reading).delete()

	@staticmethod
	def force_retrieve_hour_reading(all_grouped_sources, start_dt, hour_idx):
		logger = logging.getLogger('django.recap_data_log')

		start_time = start_dt + datetime.timedelta(hours=hour_idx)
		end_time = start_time + datetime.timedelta(minutes=59)
		end_timestamp = calendar.timegm(end_time.utctimetuple())
		reading_datetimes = [(end_time - datetime.timedelta(minutes=minute)) for minute in xrange(60)]

		logger.info('force retrieve: %s'%start_time.strftime('%Y-%m-%d %H:%M'))
		for grouped_sources in all_grouped_sources:
			xml_url = grouped_sources['_id']
			sources = grouped_sources['sources']
			logger.info('force retrieve: %s'%xml_url)

			SourceReadingMin.objects(
				source_id__in=[source['_id'] for source in sources],
				datetime__gte=start_time,
				datetime__lte=end_time
			).delete()

			source_reading_mins = []
			source_reading_mins_invalid = []
			need_update_source_ids = []
			try:
				readings = SourceManager.__get_egauge_data(xml_url, end_timestamp, 60)
				for source in sources:
					if source['name'] in readings:
						source_reading_mins += [SourceReadingMin(
							datetime=reading_datetime,
							source_id=source['_id'],
							value=readings[source['name']][idx]
						) for (idx, reading_datetime) in enumerate(reading_datetimes)]
						need_update_source_ids.append(source['_id'])
					else:
						Utils.log_error("no matching cname for source! source: %s, cname: %s"%(xml_url, source['name']))
						source_reading_mins_invalid += [SourceReadingMinInvalid(
							datetime=reading_datetime,
							source_id=source['_id'],
							xml_url=xml_url,
							name=source['name'],
							tz=source['tz']
						) for (idx, reading_datetime) in enumerate(reading_datetimes)]
			except SourceManager.GetEgaugeDataError, e:
				for source in sources:
					source_reading_mins_invalid += [SourceReadingMinInvalid(
						datetime=reading_datetime,
						source_id=source['_id'],
						xml_url=xml_url,
						name=source['name'],
						tz=source['tz']
					) for (idx, reading_datetime) in enumerate(reading_datetimes)]
			except SourceManager.TimeDeltaNotMatchError, e:
				# recover cannot handle compressed data at this stage
				# so do not add to invalid queue
				readings = SourceManager.__get_egauge_compressed_data(xml_url, end_timestamp)
				for source in sources:
					if source['name'] in readings:
						source_reading_mins += [SourceReadingMin(
							datetime=reading_datetime,
							source_id=source['_id'],
							value=(readings[source['name']][0]/60.0)
						) for (idx, reading_datetime) in enumerate(reading_datetimes)]
						need_update_source_ids.append(source['_id'])
					else:
						Utils.log_error("no matching cname for source! source: %s, cname: %s"%(xml_url, source['name']))

			if source_reading_mins:
				SourceReadingMin.objects.insert(source_reading_mins)
			if source_reading_mins_invalid:
				SourceReadingMinInvalid.objects.insert(source_reading_mins_invalid)

			if need_update_source_ids:
				source_tz = sources[0]['tz']
				SourceManager.update_sum(start_time, source_tz, need_update_source_ids)

	@staticmethod
	def force_retrieve_reading(start_dt, end_dt, system_codes, celery_task=None):
		'''
		The start_dt and end_dt should be timezone aware
		'''
		all_grouped_sources = SourceManager.get_grouped_sources(system_codes)
		start_dt = start_dt.replace(minute=0, second=0, microsecond=0)
		end_dt = end_dt.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
		total_hour = int((end_dt - start_dt).total_seconds()/3600)

		for hour_idx in xrange(total_hour):
			if celery_task is None:
				SourceManager.force_retrieve_hour_reading(all_grouped_sources, start_dt, hour_idx)
			else:
				celery_task.delay(all_grouped_sources, start_dt, hour_idx)
	@staticmethod
	def force_retrieve_all_reading(start_dt, end_dt):
		SourceManager.force_retrieve_reading(start_dt, end_dt, None)

	@staticmethod
	def __get_egauge_data(xml_url, start_timestamp, row):
		full_url = 'http://%s/cgi-bin/egauge-show/?m&n=%d&a&C&f=%d' % (xml_url, (row+1), start_timestamp)
		digest_auth = requests.auth.HTTPDigestAuth(SourceManager.DEFAULT_USERNAME, SourceManager.DEFAULT_PASSWORD)
		try:
			response = requests.get(full_url, auth=digest_auth)
		except (requests.ConnectionError, requests.exceptions.ChunkedEncodingError) as e:
			raise SourceManager.GetEgaugeDataError(str(e))

		if response.status_code != 200:
			raise SourceManager.GetEgaugeDataError("Response status code: %d"%response.status_code)
		xml_content = response.content

		root = etree.XML(xml_content)
		time_delta = int(root.find('data').get('time_delta'))
		if time_delta != 60:
			raise SourceManager.TimeDeltaNotMatchError("time_delta not match: %s"%full_url)

		cnames = [cname.text.strip() for cname in root.getiterator('cname')]
		result = {}
		for idx, cname in enumerate(cnames):
			values = root.xpath("//r[position()>1]/c[%d]/text()"%(idx+1))
			if len(values) != row:
				raise SourceManager.GetEgaugeDataError("cname or row number not much! source: %s, cname: %s, row_num: %d"%(full_url, cname, row))
			result[cname] = [abs(float(value))/3600000 for value in values]
		return result

	@staticmethod
	def __get_egauge_compressed_data(xml_url, start_timestamp):
		full_url = 'http://%s/cgi-bin/egauge-show/?h&n=2&a&C&f=%d' % (xml_url, start_timestamp)
		digest_auth = requests.auth.HTTPDigestAuth(SourceManager.DEFAULT_USERNAME, SourceManager.DEFAULT_PASSWORD)
		try:
			response = requests.get(full_url, auth=digest_auth)
		except (requests.ConnectionError, requests.exceptions.ChunkedEncodingError) as e:
			raise SourceManager.GetEgaugeDataError(str(e))

		if response.status_code != 200:
			raise SourceManager.GetEgaugeDataError("Response status code: %d"%response.status_code)
		xml_content = response.content

		root = etree.XML(xml_content)
		cnames = [cname.text.strip() for cname in root.getiterator('cname')]
		result = {}
		for idx, cname in enumerate(cnames):
			values = root.xpath("//r[position()>1]/c[%d]/text()"%(idx+1))
			if len(values) != 1:
				raise SourceManager.GetEgaugeDataError("cname or row number not much! source: %s, cname: %s, row_num: %d"%(full_url, cname, 2))
			result[cname] = [abs(float(value))/3600000 for value in values]
		return result

	@staticmethod
	def get_sources(system):
		system_code = system.code
		system_path = system.path
		if not system_path:
			target_path = ',%s,'%system_code
		else:
			target_path = '%s%s,'%(system_path, system_code)
		sources = Source.objects(Q(system_code=system_code) | Q(system_path__startswith=target_path))

		return sources

	@staticmethod
	def get_readings(source_ids, range_type, start_dt, end_dt):
		range_type_mapping = {
			Utils.RANGE_TYPE_HOUR: {'target_class': SourceReadingMin},
			Utils.RANGE_TYPE_DAY: {'target_class': SourceReadingHour},
			Utils.RANGE_TYPE_WEEK: {'target_class': SourceReadingDay},
			Utils.RANGE_TYPE_MONTH: {'target_class': SourceReadingDay},
			Utils.RANGE_TYPE_YEAR: {'target_class': SourceReadingMonth},
		}
		target_class = range_type_mapping[range_type]['target_class']

		return SourceManager.get_readings_with_target_class(source_ids, target_class, start_dt, end_dt)

	@staticmethod
	def get_readings_with_target_class(source_ids, target_class, start_dt, end_dt):
		readings = target_class.objects(
			source_id__in=source_ids,
			datetime__gte=start_dt,
			datetime__lt=end_dt)

		return SourceManager.group_readings_with_source_id(readings)

	@staticmethod
	def group_readings_with_source_id(readings):
		grouped_readings = {}

		for reading in readings:
			if str(reading.source_id) not in grouped_readings:
				grouped_readings[str(reading.source_id)] = {}

			dt_key = calendar.timegm(reading.datetime.utctimetuple())
			grouped_readings[str(reading.source_id)][dt_key] = reading.value

		return grouped_readings

	@staticmethod
	def get_most_readings(source_ids, range_type, tz_offset, sort_order, system, start_dt):
		range_type_mapping = {
			Utils.RANGE_TYPE_HOUR: {'compare_collection': 'source_reading_hour'},
			Utils.RANGE_TYPE_DAY: {'compare_collection': 'source_reading_day'},
			Utils.RANGE_TYPE_WEEK: {'compare_collection': 'source_reading_week'},
			Utils.RANGE_TYPE_MONTH: {'compare_collection': 'source_reading_month'},
			Utils.RANGE_TYPE_YEAR: {'compare_collection': 'source_reading_year'},
		}

		system_timezone = pytz.timezone(system.timezone)
		dt_lower_bound = system.first_record.astimezone(system_timezone).replace(
				hour=0, minute=0, second=0, microsecond=0)
		dt_upper_bound = pytz.utc.localize(datetime.datetime.utcnow()).astimezone(system_timezone).replace(
			minute=0, second=0, microsecond=0)
		match_condition = {'source_id': {'$in': [ObjectId(source_id) for source_id in source_ids]}}
		if range_type == Utils.RANGE_TYPE_HOUR:
			match_condition["datetime"] = {'$lt': dt_upper_bound}
		elif range_type == Utils.RANGE_TYPE_DAY:
			dt_upper_bound = dt_upper_bound.replace(hour=0)
			match_condition["datetime"] = {'$lt': dt_upper_bound}
		elif range_type == Utils.RANGE_TYPE_WEEK:
			dt_upper_bound = dt_upper_bound.replace(hour=0)
			dt_upper_bound -= datetime.timedelta(days=(dt_upper_bound.weekday()+1))
			if dt_lower_bound.weekday() != 6:
				dt_lower_bound += datetime.timedelta(days=(6-dt_lower_bound.weekday()))
			match_condition["datetime"] = {'$gte': dt_lower_bound, '$lt': dt_upper_bound}
		elif range_type == Utils.RANGE_TYPE_MONTH:
			dt_upper_bound = dt_upper_bound.replace(day=1, hour=0)
			if dt_lower_bound.day != 1:
				dt_lower_bound = Utils.add_month(dt_lower_bound, 1).replace(day=1)
			match_condition["datetime"] = {'$gte': dt_lower_bound, '$lt': dt_upper_bound}
		elif range_type == Utils.RANGE_TYPE_YEAR:
			dt_upper_bound = dt_upper_bound.replace(month=1, day=1, hour=0)
			if dt_lower_bound.month != 1 or dt_lower_bound.day != 1:
				dt_lower_bound = dt_lower_bound.replace(year=(dt_lower_bound.year+1), month=1, day=1)
			match_condition["datetime"] = {'$gte': dt_lower_bound, '$lt': dt_upper_bound}

		aggregate_pipeline = [
			{"$match": match_condition},
			{
				"$group": {
					"_id": "$datetime",
					"total": {"$sum": "$value"}
				}
			},
			{"$sort": {"total": sort_order}},
		]
		if range_type != Utils.RANGE_TYPE_DAY:
			aggregate_pipeline.append({"$limit": 1})

		mapped_info = range_type_mapping[range_type]
		current_db_conn = connection.get_db()
		result = current_db_conn[mapped_info['compare_collection']].aggregate(aggregate_pipeline)

		info = {}

		if range_type == Utils.RANGE_TYPE_DAY:
			target_weekday = start_dt.astimezone(system_timezone).weekday()
			for result_data in result["result"]:
				result_data_dt = result_data["_id"].astimezone(system_timezone)
				if result_data_dt.weekday() == target_weekday:
					result['result'] = [result_data]
					break

		if result["result"]:
			start_dt = result["result"][0]["_id"].astimezone(pytz.utc)
			end_dt = Utils.gen_end_dt(range_type, start_dt, tz_offset)

			info['timestamp'] = calendar.timegm(start_dt.utctimetuple())
			info['readings'] = SourceManager.get_readings(source_ids, range_type, start_dt, end_dt)
		else:
			info['timestamp'] = None
			info['readings'] = {}

		return info

	@staticmethod
	def get_readings_sum(source_ids, start_dt, end_dt):
		source_readings = SourceReadingMin.objects(
			source_id__in=(ObjectId(source_id) for source_id in source_ids),
			datetime__gte=start_dt,
			datetime__lt=end_dt)
		
		num_of_min_interval = len(source_readings)
		total = sum((source_reading.value for source_reading in source_readings))

		return (total, num_of_min_interval)
