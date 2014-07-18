import requests
import pytz
import calendar
import time
import datetime
from bson.code import Code
from bson.objectid import ObjectId
from mongoengine import connection, Q, NotUniqueError
from .models import Source, SourceReadingMin, SourceReadingHour,\
	SourceReadingDay, SourceReadingWeek, SourceReadingMonth, SourceReadingYear, SourceReadingMinInvalid
from lxml import etree
from collections import defaultdict
from utils.utils import Utils

class SourceManager:

	DEFAULT_USERNAME = 'owner'
	DEFAULT_PASSWORD = 'jianshu1906'

	class GetEgaugeDataError(Exception):
		pass

	@staticmethod
	def get_grouped_sources():
		current_db_conn = connection.get_db()
		result = current_db_conn.source.aggregate([
			{ "$project": {"_id": 1, "name": 1, "tz": 1, "xml_url": 1}},
			{
				"$group": {
					"_id": "$xml_url",
					"sources": {"$push": {"_id": "$_id", "name": "$name", "tz": "$tz"}}
				}
			}
		])

		return result['result']

	@staticmethod
	def gen_retrieve_time():
		retrieve_time = datetime.datetime.utcnow()
		retrieve_time = pytz.utc.localize(retrieve_time.replace(second=0, microsecond=0))
		# delay 1 seconds to ensure data at meter is ready
		retrieve_time -= datetime.timedelta(minutes=1)

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
					source_reading_mins_invalid = SourceReadingMinInvalid(**construct_info)
					source_reading_mins_invalid.append(source_reading_mins_invalid)
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
	def get_grouped_invalid_readings():
		current_db_conn = connection.get_db()
		result = current_db_conn['source_reading_min_invalid'].aggregate([
			{
				"$group": {
					"_id": {"xml_url": "$xml_url", "datetime": "$datetime"},
					"sources": {"$push": {"_id": "$_id", "source_id": "$source_id", "name": "$name", "tz":"$tz"}}
				}
			}
		])

		return result['result']

	@staticmethod
	def recover_all_invalid_reading():
		grouped_invalid_readings = SourceManager.get_grouped_invalid_readings()
		for grouped_invalid_reading in grouped_invalid_readings:
			SourceManager.recover_min_reading(grouped_invalid_reading)

	@staticmethod
	def recover_min_reading(grouped_invalid_reading):
		xml_url = grouped_invalid_reading['_id']['xml_url']
		retrieve_time = pytz.utc.localize(grouped_invalid_reading['_id']['datetime'])
		sources = grouped_invalid_reading['sources']

		start_timestamp = calendar.timegm(retrieve_time.utctimetuple())
		try:
			source_reading_mins = []
			need_update_source_ids = []
			will_remove_invalid_reading = []
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
					will_remove_invalid_reading.append(source['_id'])
				else:
					# do nothing
					pass
		except SourceManager.GetEgaugeDataError, e:
			# do nothing
			pass

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
	def force_retrieve_all_reading(start_dt, end_dt):
		'''
		The start_dt and end_dt should be timezone aware
		'''
		all_grouped_sources = SourceManager.get_grouped_sources()
		start_dt = start_dt.replace(minute=0, second=0, microsecond=0)
		end_dt = end_dt.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(hours=1)
		total_hour = int((end_dt - start_dt).total_seconds()/3600)

		for hour_idx in xrange(total_hour):
			start_time = start_dt + datetime.timedelta(hours=hour_idx)
			end_time = start_time + datetime.timedelta(minutes=59)
			end_timestamp = calendar.timegm(end_time.utctimetuple())
			reading_datetimes = [(end_time - datetime.timedelta(minutes=minute)) for minute in xrange(60)]

			print 'processing: ', start_time
			for grouped_sources in all_grouped_sources:
				xml_url = grouped_sources['_id']
				sources = grouped_sources['sources']
				print 'processing: ', xml_url

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

				if source_reading_mins:
					SourceReadingMin.objects.insert(source_reading_mins)
				if source_reading_mins_invalid:
					SourceReadingMinInvalid.objects.insert(source_reading_mins_invalid)

				if need_update_source_ids:
					source_tz = sources[0]['tz']
					SourceManager.update_sum(start_time, source_tz, need_update_source_ids)

	@staticmethod
	def __get_egauge_data(xml_url, start_timestamp, row):
		full_url = 'http://%s/cgi-bin/egauge-show/?m&n=%d&a&C&f=%d' % (xml_url, (row+1), start_timestamp)
		digest_auth = requests.auth.HTTPDigestAuth(SourceManager.DEFAULT_USERNAME, SourceManager.DEFAULT_PASSWORD)
		try:
			response = requests.get(full_url, auth=digest_auth)
		except requests.ConnectionError, e:
			raise SourceManager.GetEgaugeDataError(str(e))

		if response.status_code != 200:
			raise SourceManager.GetEgaugeDataError("Response status code: %d"%response.status_code)
		xml_content = response.content

		root = etree.XML(xml_content)
		cnames = [cname.text.strip() for cname in root.getiterator('cname')]
		result = {}
		for idx, cname in enumerate(cnames):
			values = root.xpath("//r[position()>1]/c[%d]/text()"%(idx+1))
			if len(values) != row:
				raise SourceManager.GetEgaugeDataError("cname or row number not much! source: %s, cname: %s, row_num: %d"%(full_url, cname, row))
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
	def get_most_readings(source_ids, range_type, tz_offset, sort_order):
		range_type_mapping = {
			Utils.RANGE_TYPE_HOUR: {'compare_collection': 'source_reading_hour'},
			Utils.RANGE_TYPE_DAY: {'compare_collection': 'source_reading_day'},
			Utils.RANGE_TYPE_WEEK: {'compare_collection': 'source_reading_week'},
			Utils.RANGE_TYPE_MONTH: {'compare_collection': 'source_reading_month'},
			Utils.RANGE_TYPE_YEAR: {'compare_collection': 'source_reading_year'},
		}

		mapped_info = range_type_mapping[range_type]
		current_db_conn = connection.get_db()
		result = current_db_conn[mapped_info['compare_collection']].aggregate([
			{"$match": {'source_id': {'$in': [ObjectId(source_id) for source_id in source_ids]}}},
			{
				"$group": {
					"_id": "$datetime",
					"total": {"$sum": "$value"}
				}
			},
			{"$sort": {"total": sort_order}},
			{"$limit": 1}
		])

		start_dt = pytz.utc.localize(result["result"][0]["_id"])
		end_dt = Utils.gen_end_dt(range_type, start_dt, tz_offset)

		info = {}
		info['timestamp'] = calendar.timegm(start_dt.utctimetuple())
		info['readings'] = SourceManager.get_readings(source_ids, range_type, start_dt, end_dt)

		return info
