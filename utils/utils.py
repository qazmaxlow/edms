import logging
import datetime
import json
import pytz
import math
import calendar
from django.http import HttpResponse

class Utils:

    LOGGER_NAME = 'django.entrak_error'
    RANGE_TYPE_MIN      = 'min'
    RANGE_TYPE_HOUR     = 'hour'
    RANGE_TYPE_DAY      = 'day'
    RANGE_TYPE_WEEK     = 'week'
    RANGE_TYPE_MONTH    = 'month'
    RANGE_TYPE_YEAR     = 'year'

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
            end_time = Utils.add_month(start_time, 1)
        elif range_type == Utils.RANGE_TYPE_YEAR:
            start_time = input_datetime.replace(month=1, day=1, hour=0, minute=0)
            end_time = start_time.replace(year=(start_time.year+1))

        return (start_time, end_time)

    @staticmethod
    def add_month(target_dt, val):
        result_month = target_dt.month - 1 + val
        result_year = target_dt.year + (result_month/12)
        result_month = result_month % 12 + 1
        result_day = min(target_dt.day, calendar.monthrange(result_year, result_month)[1])

        return target_dt.replace(year=result_year, month=result_month, day=result_day)

    @staticmethod
    def add_year(target_dt, val):
        result_year = target_dt.year + val
        result_day = min(target_dt.day, calendar.monthrange(result_year, target_dt.month)[1])

        return target_dt.replace(year=result_year, day=result_day)

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
            end_dt = Utils.add_month(transform_dt, 1)
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

    @staticmethod
    def gen_source_group_map(grouped_source_infos):
        source_group_map = {}
        for group_idx, source_info in enumerate(grouped_source_infos):
            for source_id in source_info['source_ids']:
                source_group_map[source_id] = group_idx

        return source_group_map

    @staticmethod
    def get_source_ids_from_grouped_source_info(grouped_source_infos):
        return reduce(
            lambda source_ids, source_info: source_ids+source_info['source_ids'],
            grouped_source_infos, [])
