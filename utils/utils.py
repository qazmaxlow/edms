import logging
import datetime
import json
import pytz
from django.http import HttpResponse

class Utils:

	LOGGER_NAME = 'django.entrak_error'
	RANGE_TYPE_MIN		= 'min'
	RANGE_TYPE_HOUR		= 'hour'
	RANGE_TYPE_DAY		= 'day'
	RANGE_TYPE_WEEK		= 'week'
	RANGE_TYPE_MONTH	= 'month'
	RANGE_TYPE_YEAR		= 'year'

	@staticmethod
	def log_exception(error):
		logger = logging.getLogger(Utils.LOGGER_NAME)
		logger.exception(error)

	@staticmethod
	def log_error(msg):
		logger = logging.getLogger(Utils.LOGGER_NAME)
		logger.error(msg)

	@staticmethod
	def get_datetime_range(range_type, input_datetime):
		if range_type == Utils.RANGE_TYPE_HOUR:
			start_time = input_datetime.replace(minute=0)
			end_time = start_time + datetime.timedelta(hours=1)
		elif range_type == Utils.RANGE_TYPE_DAY:
			start_time = input_datetime.replace(hour=0, minute=0)
			end_time = start_time + datetime.timedelta(days=1)
		elif range_type == Utils.RANGE_TYPE_WEEK:
			start_time = input_datetime.replace(hour=0, minute=0)
			start_time = start_time - datetime.timedelta(days=(start_time.weekday()+1))
			end_time = start_time + datetime.timedelta(days=7)
		elif range_type == Utils.RANGE_TYPE_MONTH:
			start_time = input_datetime.replace(day=1, hour=0, minute=0)
			if start_time.month == 12:
				end_time = start_time.replace(year=(start_time.year+1), month=1)
			else:
				end_time = start_time.replace(month=(start_time.month+1))
		elif range_type == Utils.RANGE_TYPE_YEAR:
			start_time = input_datetime.replace(month=1, day=1, hour=0, minute=0)
			end_time = start_time.replace(year=(start_time.year+1))

		return (start_time, end_time)

	@staticmethod
	def gen_end_dt(range_type, start_dt, tz_offset):
		if range_type == Utils.RANGE_TYPE_HOUR:
			end_dt = start_dt + datetime.timedelta(hours=1)
		elif range_type == Utils.RANGE_TYPE_DAY:
			end_dt = start_dt + datetime.timedelta(days=1)
		elif range_type == Utils.RANGE_TYPE_WEEK:
			end_dt = start_dt + datetime.timedelta(days=7)
		elif range_type == Utils.RANGE_TYPE_MONTH:
			transform_dt = start_dt - datetime.timedelta(hours=tz_offset)
			if transform_dt.month == 12:
				end_dt = transform_dt.replace(year=(transform_dt.year+1), month=1)
			else:
				end_dt = transform_dt.replace(month=(transform_dt.month+1))
			end_dt += datetime.timedelta(hours=tz_offset)
		elif range_type == Utils.RANGE_TYPE_YEAR:
			end_dt = start_dt.replace(year=(start_dt.year+1))

		return end_dt

	@staticmethod
	def json_response(data):
		return HttpResponse(json.dumps(data), content_type="application/json")

	@staticmethod
	def utc_dt_from_utc_timestamp(timestamp):
		return datetime.datetime.fromtimestamp(timestamp, pytz.utc)
