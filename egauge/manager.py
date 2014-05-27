import requests
import pytz
from bson.code import Code
from models import Source, SourceReadingMin
import time
import datetime
from lxml import etree
from utils.utils import Utils

class SourceManager:

	DEFAULT_USERNAME = 'owner'
	DEFAULT_PASSWORD = 'default'

	class GetEgaugeDataError(Exception):
		pass

	map_xml_url = Code('''
		function () {
			emit(this.xml_url, {
				source_id: this._id,
				name: this.name,
			});
		}
	''')

	# reduce function cannot ouput array, so use dict
	reduce_xml_url = Code('''
		function (key, values) {
			result = {reduced: true};
			for (var idx = 0; idx < values.length; idx++){
				result[idx] = values[idx];
			}
			return result;
		}
	''')

	@staticmethod
	def retrieveAllReading():
		grouped_sources = Source.objects.map_reduce(SourceManager.map_xml_url, SourceManager.reduce_xml_url, 'inline')
		for document in grouped_sources:
			xml_url = document.key
			value = document.value
			start_timestamp = int(time.time())

			# reduced boolean is added as some mapping may not go through reduce function
			# if the mapped value count is only one
			if 'reduced' in value:
				del value['reduced']
				SourceManager.retrieveReading(xml_url, value, start_timestamp)
			else:
				SourceManager.retrieveReading(xml_url, {u'0': value}, start_timestamp)

	@staticmethod
	def retrieveReading(xml_url, infos, start_timestamp):
		source_reading_mins = []
		reading_datetime = datetime.datetime.fromtimestamp(start_timestamp).replace(tzinfo=pytz.timezone("UTC"))
		try:
			readings = SourceManager.getEgaugeData(xml_url, start_timestamp, 2)
			for dummy, info in infos.items():
				source_reading_min = SourceReadingMin(
					datetime=reading_datetime,
					source_id=info['source_id'],
					name=info['name'],
					xml_url=xml_url,
				)
				if info['name'] in readings:
					source_reading_min.value = readings[info['name']]
					source_reading_min.valid = True
				else:
					Utils.log_error("no matching cname for source! source: %s, cname: %s"%(xml_url, info['name']))
					source_reading_min.value = 0
					source_reading_min.valid = False
				source_reading_mins.append(source_reading_min)
		except SourceManager.GetEgaugeDataError, e:
			source_reading_mins = [SourceReadingMin(
					datetime=reading_datetime,
					source_id=info['source_id'],
					name=info['name'],
					xml_url=xml_url,
					value=0,
					valid=False
			) for (dummy, info) in infos.items()]
			Utils.log_exception(e)

		SourceReadingMin.objects.insert(source_reading_mins)

	@staticmethod
	def getEgaugeData(xml_url, start_timestamp, row):
		full_url = 'http://%s/cgi-bin/egauge-show/?m&n=%d&a&C&f=%d' % (xml_url, row, start_timestamp)
		digest_auth = requests.auth.HTTPDigestAuth(SourceManager.DEFAULT_USERNAME, SourceManager.DEFAULT_PASSWORD)
		response = requests.get(full_url, auth=digest_auth)
		if response.status_code != 200:
			raise SourceManager.GetEgaugeDataError("Response status code: %d"%response.status_code)
		xml_content = response.content

		root = etree.XML(xml_content)
		cnames = [cname.text.strip() for cname in root.getiterator('cname')]
		values = [abs(float(value))/3600000 for value in root.xpath("//r[2]/c/text()")]
		if len(cnames) != len(values):
			raise SourceManager.GetEgaugeDataError("cnames and values number not much! source: %s"%xml_url)

		return dict(zip(cnames, values))
