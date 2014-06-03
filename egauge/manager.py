import requests
import pytz
from bson.code import Code
from mongoengine import connection
from .models import Source, SourceReadingMin, SourceReadingHour,\
	SourceReadingDay, SourceReadingWeek, SourceReadingMonth, SourceReadingYear, SourceReadingMinInvalid
import time
import datetime
from lxml import etree
from utils.utils import Utils

class SourceManager:

	DEFAULT_USERNAME = 'owner'
	DEFAULT_PASSWORD = 'default'

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
		retrieve_time = retrieve_time.replace(second=0, microsecond=0, tzinfo=pytz.timezone("UTC"))
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
		start_timestamp = time.mktime(retrieve_time.utctimetuple())
		try:
			readings = SourceManager._get_egauge_data(xml_url, start_timestamp, 2)
			for info in infos:
				construct_info = {
					'datetime': retrieve_time,
					'source_id': info['_id'],
				}
				if info['name'] in readings:
					construct_info['value'] = readings[info['name']]
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
		retrieve_time = (grouped_invalid_reading['_id']['datetime']).replace(tzinfo=pytz.timezone("UTC"))
		sources = grouped_invalid_reading['sources']

		start_timestamp = time.mktime(retrieve_time.utctimetuple())
		try:
			source_reading_mins = []
			need_update_source_ids = []
			will_remove_invalid_reading = []
			readings = SourceManager._get_egauge_data(xml_url, start_timestamp, 2)
			for source in sources:
				if source['name'] in readings:
					source_reading_min = SourceReadingMin(
						datetime=retrieve_time,
						source_id=source['source_id'],
						value=readings[source['name']]
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
			SourceReadingMin.objects.insert(source_reading_mins)
		if need_update_source_ids:
			source_tz = sources[0]['tz']
			SourceManager.update_sum(retrieve_time, source_tz, need_update_source_ids)
		if will_remove_invalid_reading:
			SourceReadingMinInvalid.objects(id__in=will_remove_invalid_reading).delete()

	@staticmethod
	def _get_egauge_data(xml_url, start_timestamp, row):
		full_url = 'http://%s/cgi-bin/egauge-show/?m&n=%d&a&C&f=%d' % (xml_url, row, start_timestamp)
		# full_url = 'http://%s/cgi-bin/egauge-show/?m&n=%d&a&f=%d' % (xml_url, row, start_timestamp)
		digest_auth = requests.auth.HTTPDigestAuth(SourceManager.DEFAULT_USERNAME, SourceManager.DEFAULT_PASSWORD)
		response = requests.get(full_url, auth=digest_auth)
		if response.status_code != 200:
			raise SourceManager.GetEgaugeDataError("Response status code: %d"%response.status_code)
		xml_content = response.content

		root = etree.XML(xml_content)
		cnames = [cname.text.strip() for cname in root.getiterator('cname')]
		# current_values = [float(value)/3600000 for value in root.xpath("//r[1]/c/text()")]
		# past_values = [float(value)/3600000 for value in root.xpath("//r[2]/c/text()")]
		# if not (len(current_values) == len(past_values) == len(cnames)):
		# 	raise SourceManager.GetEgaugeDataError("cnames and values number not much! source: %s"%full_url)
		# values = map((lambda current_v,past_v:abs(current_v-past_v)), current_values, past_values)
		values = [abs(float(value))/3600000 for value in root.xpath("//r[2]/c/text()")]
		if len(cnames) != len(values):
			Utils.log_error(xml_content)
			raise SourceManager.GetEgaugeDataError("cnames and values number not much! source: %s"%full_url)

		return dict(zip(cnames, values))
