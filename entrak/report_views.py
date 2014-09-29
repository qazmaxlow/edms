import os
import sys
import pytz
import datetime
import copy
import json
import operator
import calendar
import pdfkit
import uuid
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.core.urlresolvers import reverse
from django.core.context_processors import csrf
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Q
from django.utils.html import escapejs
from mongoengine import Q as MongoQ
from entrak.settings import MEDIA_ROOT
from system.models import System
from unit.models import UnitRate, CO2_CATEGORY_CODE, MONEY_CATEGORY_CODE
from baseline.models import BaselineUsage
from egauge.manager import SourceManager
from egauge.models import SourceReadingMonth, SourceReadingDay, SourceReadingHour
from utils.auth import permission_required
from utils.utils import Utils
from utils import calculation

TEMP_MEDIA_DIR = os.path.join(MEDIA_ROOT, 'temp')
REPORT_TYPE_MONTH = 'month'
REPORT_TYPE_YEAR = 'year'
REPORT_TYPE_QUARTER = 'quarter'
REPORT_TYPE_CUSTOM_MONTH = 'custom-month'
REPORT_TYPE_WEEK = 'week'

CONSECUTIVE_LASTS_COUNT = 4

@permission_required()
@ensure_csrf_cookie
def report_view(request, system_code=None):
	systems_info = System.get_systems_info(system_code, request.user.system.code)
	systems = systems_info['systems']
	current_system = systems[0]
	sources = SourceManager.get_sources(current_system)

	current_system_tz = pytz.timezone(current_system.timezone)
	first_record = min([system.first_record for system in systems])
	first_record = first_record.astimezone(current_system_tz).replace(
		hour=0, minute=0, second=0, microsecond=0)
	if first_record.day == 1:
		start_dt = first_record
	else:
		start_dt = Utils.add_month(first_record, 1).replace(day=1)

	end_dt = pytz.utc.localize(datetime.datetime.utcnow()).astimezone(current_system_tz)
	end_dt = end_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

	source_ids = [str(source.id) for source in sources]
	source_readings = SourceManager.get_readings_with_target_class(source_ids, SourceReadingMonth, start_dt, end_dt)
	energy_usages = calculation.combine_readings_by_timestamp(source_readings)

	unit_rates = UnitRate.objects.filter(Q(category_code=CO2_CATEGORY_CODE) | Q(category_code=MONEY_CATEGORY_CODE))
	co2_unit_rates = [unit_rate for unit_rate in unit_rates if unit_rate.category_code == CO2_CATEGORY_CODE]
	money_unit_rates = [unit_rate for unit_rate in unit_rates if unit_rate.category_code == MONEY_CATEGORY_CODE]

	co2_usages = copy.deepcopy(source_readings)
	calculation.transform_source_readings(co2_usages, systems, sources, co2_unit_rates, CO2_CATEGORY_CODE)
	co2_usages = calculation.combine_readings_by_timestamp(co2_usages)

	money_usages = copy.deepcopy(source_readings)
	calculation.transform_source_readings(money_usages, systems, sources, money_unit_rates, MONEY_CATEGORY_CODE)
	money_usages = calculation.combine_readings_by_timestamp(money_usages)

	monthly_summary = []
	for timestamp, usage in energy_usages.items():
		monthly_summary.append({
			'dt': Utils.utc_dt_from_utc_timestamp(timestamp).astimezone(current_system_tz),
			'timestamp': timestamp,
			'energy_usage': usage, 'co2_usage': co2_usages[timestamp],
			'money_usage': money_usages[timestamp]})

	m = systems_info
	m["monthly_summary"] = sorted(monthly_summary, key=lambda x: x['timestamp'], reverse=True)
	m.update(csrf(request))

	return render_to_response('report.html', m)

def __calculcate_total_max_min(readings, timezone):
	total_val = 0
	total_day = 0
	max_usage_val = 0
	max_usage_date = None
	min_usage_val = sys.float_info.max
	min_usage_date = None
	for timestamp, val in readings.items():
		dt = Utils.utc_dt_from_utc_timestamp(timestamp).astimezone(timezone)
		total_val += val
		total_day += 1
		if val >= max_usage_val:
			max_usage_val = val;
			max_usage_date = dt.date()

		if val <= min_usage_val:
			min_usage_val = val;
			min_usage_date = dt.date()

	if max_usage_date is None:
		max_usage_val = None
	else:
		max_usage_date = max_usage_date.strftime("%Y-%m-%d")
	if min_usage_date is None:
		min_usage_val = None
	else:
		min_usage_date = min_usage_date.strftime("%Y-%m-%d")

	return {
		'total': total_val,
		'average': (total_val/total_day) if (total_day != 0) else 0,
		'max': {'date': max_usage_date, 'val': max_usage_val},
		'min': {'date': min_usage_date, 'val': min_usage_val},
	}

def __calculate_weekday_info(readings, holidays, timezone):
	filterd_readings = {}
	for timestamp, val in readings.items():
		dt = Utils.utc_dt_from_utc_timestamp(timestamp).astimezone(timezone)
		if dt.weekday() <= 4 and (dt.date() not in holidays):
			filterd_readings[timestamp] = val

	return __calculcate_total_max_min(filterd_readings, timezone)

def __calculate_weekend_info(readings, timezone):
	filterd_readings = {}
	for timestamp, val in readings.items():
		dt = Utils.utc_dt_from_utc_timestamp(timestamp).astimezone(timezone)
		if dt.weekday() >= 5:
			filterd_readings[timestamp] = val

	return __calculcate_total_max_min(filterd_readings, timezone)

def __calculate_overnight_info(readings, timezone):
	return __calculcate_total_max_min(readings, timezone)

def __transform_to_daily_overnight_readings(source_readings, timezone, night_time_start, night_time_end):
	result = {}
	for source_id, readings in source_readings.items():
		result[source_id] = {}
		for timestamp, val in readings.items():
			dt = Utils.utc_dt_from_utc_timestamp(timestamp).astimezone(timezone)
			if dt.time() >= night_time_start:
				target_dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
			elif dt.time() < night_time_end:
				target_dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
				target_dt -= datetime.timedelta(days=1)
			else:
				target_dt = None

			if target_dt is not None:
				target_timestamp = calendar.timegm(target_dt.utctimetuple())
				result[source_id][target_timestamp] = val + result[source_id].get(target_timestamp, 0)

	return result

def __get_sum_up_usage_within_periods(source_ids, period_dts, target_period_num):
	if period_dts:
		start_dt = period_dts[-1]['start_dt']
		end_dt = period_dts[0]['end_dt']
		source_readings = SourceReadingDay.objects(source_id__in=source_ids, datetime__gte=start_dt, datetime__lt=end_dt)
	else:
		source_readings = []

	results = [0]*len(period_dts)
	for source_reading in source_readings:
		reading_dt = source_reading.datetime.astimezone(pytz.utc)

		for period_idx in xrange(len(period_dts)):
			bound_start = period_dts[period_idx]['start_dt']
			bound_end = period_dts[period_idx]['end_dt']
			if reading_dt >= bound_start and reading_dt < bound_end:
				results[period_idx] += source_reading.value
				break

	if len(period_dts) != target_period_num:
		missing_period_num = target_period_num-len(period_dts)
		results += ([0]*missing_period_num)

	return results

def __gen_report_last_dt(report_type, target_dt, day_diff=None):
	if report_type == REPORT_TYPE_MONTH:
		result = Utils.add_month(target_dt, -1)
	elif report_type == REPORT_TYPE_YEAR:
		result = Utils.add_year(target_dt, -1)
	elif report_type == REPORT_TYPE_QUARTER:
		result = Utils.add_month(target_dt, -3)
	elif report_type == REPORT_TYPE_CUSTOM_MONTH:
		result = target_dt - datetime.timedelta(days=day_diff)
	elif report_type == REPORT_TYPE_WEEK:
		result = target_dt - datetime.timedelta(days=7)

	return result

def __gen_consecutive_lasts(report_type, target_dt, num_of_last, system_first_record, day_diff=None):
	result = []
	next_dt = target_dt
	for idx in xrange(num_of_last):
		end_dt = next_dt
		next_dt = __gen_report_last_dt(report_type, next_dt, day_diff)
		if next_dt < system_first_record:
			break

		result.append({"start_dt": next_dt, "end_dt": end_dt})

	return result

def __gen_report_dt_info(report_type, timezone, system_first_record, start_timestamp, end_timestamp):
	dt_info = {}

	start_dt = Utils.utc_dt_from_utc_timestamp(start_timestamp).astimezone(timezone)
	dt_info['start_dt'] = start_dt

	day_diff = None
	if report_type == REPORT_TYPE_MONTH:
		end_dt = Utils.add_month(start_dt, 1)
	elif report_type == REPORT_TYPE_YEAR:
		end_dt = Utils.add_year(start_dt, 1)
	elif report_type == REPORT_TYPE_QUARTER:
		end_dt = Utils.add_month(start_dt, 3)
	elif report_type == REPORT_TYPE_CUSTOM_MONTH:
		end_dt = Utils.utc_dt_from_utc_timestamp(end_timestamp).astimezone(timezone)
		day_diff = (end_dt - start_dt).days
	elif report_type == REPORT_TYPE_WEEK:
		end_dt = start_dt + datetime.timedelta(days=7)
	dt_info['end_dt'] = end_dt

	system_first_record = system_first_record.astimezone(timezone).replace(hour=0, minute=0, second=0, microsecond=0)
	if system_first_record.day == 1:
		beginning_start_dt = system_first_record
	else:
		beginning_start_dt = Utils.add_month(system_first_record.replace(day=1), 1)
	dt_info['beginning_start_dt'] = beginning_start_dt
	if report_type == REPORT_TYPE_CUSTOM_MONTH:
		dt_info['beginning_end_dt'] = beginning_start_dt + datetime.timedelta(days=day_diff)
	else:
		dt_info['beginning_end_dt'] = Utils.add_month(beginning_start_dt, 1)

	dt_info['last_same_period_start_dt'] = Utils.add_year(start_dt, -1)
	dt_info['last_same_period_end_dt'] = Utils.add_year(end_dt, -1)

	last_start_dt = __gen_report_last_dt(report_type, start_dt, day_diff)
	dt_info['last_start_dt'] = last_start_dt
	dt_info['last_end_dt'] = start_dt

	dt_info['consecutive_lasts'] = __gen_consecutive_lasts(report_type, last_start_dt,
		CONSECUTIVE_LASTS_COUNT, system_first_record, day_diff)

	return dt_info

def __generate_report_data(systems, report_type, start_timestamp, end_timestamp):
	current_system = systems[0]
	system_code = current_system.code
	current_system_timezone = pytz.timezone(current_system.timezone)

	dt_info = __gen_report_dt_info(report_type, current_system_timezone,
		current_system.first_record, start_timestamp, end_timestamp)

	sources = SourceManager.get_sources(current_system)
	source_ids = [str(source.id) for source in sources]
	timestamp_info = {
		'currentReadings': {'start': dt_info['start_dt'], 'end': dt_info['end_dt']},
		'beginningReadings': {'start': dt_info['beginning_start_dt'], 'end': dt_info['beginning_end_dt']},
	}
	if report_type != REPORT_TYPE_YEAR \
		and dt_info['last_same_period_start_dt'] >= current_system.first_record:
		timestamp_info['lastSamePeriodReadings'] = {'start': dt_info['last_same_period_start_dt'],
			'end': dt_info['last_same_period_end_dt']}
	if dt_info['last_start_dt'] >= current_system.first_record:
		timestamp_info['lastReadings'] = {'start': dt_info['last_start_dt'], 'end': dt_info['last_end_dt']}
	timestamp_bounds = reduce(
		operator.or_,
		[MongoQ(datetime__gte=info['start'], datetime__lt=info['end']) for (key, info) in timestamp_info.items()])
	source_readings = SourceReadingDay.objects(timestamp_bounds, source_id__in=source_ids)
	source_readings = SourceManager.group_readings_with_source_id(source_readings)

	grouped_source_infos = []
	for source in sources:
		if source.system_code == system_code:
			grouped_source_infos.append({"systemCode": system_code,
				"sourceIds": [str(source.id)], "sourceName": source.d_name, "sourceOrder": source.order})
		else:
			system_path_components = [code for code in source.system_path.split(',') if code != '']
			system_path_idx = system_path_components.index(system_code)
			if system_path_idx+1 >= len(system_path_components):
				grouped_system_code = source.system_code
			else:
				grouped_system_code = system_path_components[system_path_idx+1]
			match_group_idx = None
			for group_idx, info in enumerate(grouped_source_infos):
				if grouped_system_code == info["systemCode"]:
					match_group_idx = group_idx
					break

			if match_group_idx is None:
				grouped_source_infos.append({"systemCode": grouped_system_code, "sourceIds": [str(source.id)]})
			else:
				grouped_source_infos[match_group_idx]["sourceIds"].append(str(source.id))

	source_group_map = {}
	for group_idx, info in enumerate(grouped_source_infos):
		info["currentTotalEnergy"] = 0
		info["currentTotalCo2"] = 0
		info["currentTotalMoney"] = 0
		info["lastTotalEnergy"] = 0

		for source_id in info["sourceIds"]:
			source_group_map[source_id] = group_idx

			info["currentReadings"] = {}
			info["lastReadings"] = {}
			info["beginningReadings"] = {}
			info["lastSamePeriodReadings"] = {}
			info["overnightcurrentReadings"] = {}
			info["overnightlastReadings"] = {}
			info["overnightbeginningReadings"] = {}
			info["overnightlastSamePeriodReadings"] = {}

	unit_rates = UnitRate.objects.filter(Q(category_code=CO2_CATEGORY_CODE) | Q(category_code=MONEY_CATEGORY_CODE))
	co2_unit_rates = [unit_rate for unit_rate in unit_rates if unit_rate.category_code == CO2_CATEGORY_CODE]
	money_unit_rates = [unit_rate for unit_rate in unit_rates if unit_rate.category_code == MONEY_CATEGORY_CODE]
	system_source_mapping = calculation.gen_source_system_mapping(systems, sources)

	for source_id, readings in source_readings.items():
		unit_info = json.loads(system_source_mapping[source_id].unit_info)
		co2_unit_rate_code = unit_info[CO2_CATEGORY_CODE]
		money_unit_rate_code = unit_info[MONEY_CATEGORY_CODE]

		target_info = grouped_source_infos[source_group_map[source_id]]
		for timestamp, val in readings.items():
			reading_dt = Utils.utc_dt_from_utc_timestamp(timestamp)
			for name, bound_info in timestamp_info.items():
				if reading_dt >= bound_info['start'] and reading_dt < bound_info['end']:
					target_info[name][timestamp] = val + target_info[name].get(timestamp, 0)

					if name == "currentReadings":
						target_info["currentTotalEnergy"] += val
						target_info["currentTotalCo2"] += calculation.transform_reading(
							co2_unit_rate_code, timestamp, val, co2_unit_rates)
						target_info["currentTotalMoney"] += calculation.transform_reading(
							money_unit_rate_code, timestamp, val, money_unit_rates)
					elif name == "lastReadings":
						target_info["lastTotalEnergy"] += val

	overnight_timestamp_bounds = reduce(
		operator.or_,
		[MongoQ(
			datetime__gte=(info['start']-datetime.timedelta(days=1)),
			datetime__lt=(info['end']+datetime.timedelta(days=1))) for (key, info) in timestamp_info.items()])
	overnight_source_readings = SourceReadingHour.objects(overnight_timestamp_bounds, source_id__in=source_ids)
	overnight_source_readings = SourceManager.group_readings_with_source_id(overnight_source_readings)
	overnight_source_readings = __transform_to_daily_overnight_readings(overnight_source_readings, current_system_timezone,
		current_system.night_time_start, current_system.night_time_end)
	for source_id, readings in overnight_source_readings.items():
		target_info = grouped_source_infos[source_group_map[source_id]]
		for timestamp, val in readings.items():
			reading_dt = Utils.utc_dt_from_utc_timestamp(timestamp)
			for name, bound_info in timestamp_info.items():
				if reading_dt >= bound_info['start'] and reading_dt < bound_info['end']:
					overnight_name = "overnight"+name
					target_info[overnight_name][timestamp] = val + target_info[overnight_name].get(timestamp, 0)

	total_energy = 0
	last_total_energy = 0
	all_holidays = current_system.get_all_holidays(timestamp_info)
	for info in grouped_source_infos:
		total_energy += info['currentTotalEnergy']
		last_total_energy += info['lastTotalEnergy']

		calculate_info = [
			{'targetReadings': 'currentReadings', 'keyPrefix': 'current'},
			{'targetReadings': 'lastReadings', 'keyPrefix': 'last'},
			{'targetReadings': 'beginningReadings', 'keyPrefix': 'beginning'},
			{'targetReadings': 'lastSamePeriodReadings', 'keyPrefix': 'lastSamePeriod'},
		]

		for cal_info in calculate_info:
			info[cal_info['keyPrefix']+'WeekdayInfo'] = __calculate_weekday_info(info[cal_info["targetReadings"]],
				all_holidays, current_system_timezone)
			info[cal_info['keyPrefix']+'WeekendInfo'] = __calculate_weekend_info(info[cal_info["targetReadings"]],
				current_system_timezone)
			overnight_name = "overnight"+cal_info["targetReadings"]
			info[cal_info['keyPrefix']+'OvernightInfo'] = __calculate_overnight_info(info[overnight_name], current_system_timezone)

	total_baseline_energy = 0
	need_calculate_systems = System.assign_source_under_system(systems, sources)
	grouped_baselines = BaselineUsage.get_baselines_for_systems([system.id for system in need_calculate_systems.keys()])
	for system, attached_sources in need_calculate_systems.items():
		system_timezone = pytz.timezone(system.timezone)

		baselines = grouped_baselines[system.id]
		baseline_daily_usages = BaselineUsage.transform_to_daily_usages(baselines, system_timezone)
		total_baseline_energy += calculation.calculate_total_baseline_energy_usage(
			dt_info['start_dt'].astimezone(system_timezone), dt_info['end_dt'].astimezone(system_timezone), baseline_daily_usages)

	saving_info = {}
	unit_info = json.loads(current_system.unit_info)
	co2_unit_code = unit_info[CO2_CATEGORY_CODE]
	money_unit_code = unit_info[MONEY_CATEGORY_CODE]
	energy_saving = total_baseline_energy-total_energy
	saving_info["energy"] = energy_saving/total_baseline_energy*100
	saving_info["co2"] = calculation.transform_reading(co2_unit_code, start_timestamp, energy_saving, co2_unit_rates)
	saving_info["money"] = calculation.transform_reading(money_unit_code, start_timestamp, energy_saving, money_unit_rates)

	sum_up_usages = __get_sum_up_usage_within_periods(source_ids, dt_info['consecutive_lasts'], CONSECUTIVE_LASTS_COUNT)
	sum_up_usages.insert(0, total_energy)
	sum_up_usages.insert(1, last_total_energy)

	result = {}
	result['savingInfo'] = saving_info
	result['holidays'] = [holiday.strftime("%Y-%m-%d") for holiday in all_holidays]
	result['sumUpUsages'] = sum_up_usages
	result['overnightStartHr'] = current_system.night_time_start.hour
	result['overnightStartMin'] = current_system.night_time_start.minute
	result['overnightEndHr'] = current_system.night_time_end.hour
	result['overnightEndMin'] = current_system.night_time_end.minute

	for info in grouped_source_infos:
		for will_remove_data in ['beginningReadings', 'lastSamePeriodReadings',
			'overnightlastReadings', 'overnightbeginningReadings', 'overnightlastSamePeriodReadings']:
			info.pop(will_remove_data, None)
	result['groupedSourceInfos'] = grouped_source_infos

	return result

@permission_required()
def report_data_view(request, system_code=None):
	report_type = request.POST.get('report_type')
	start_timestamp = int(request.POST.get('start_timestamp'))
	end_timestamp = int(request.POST.get('end_timestamp'))

	systems = System.get_systems_within_root(system_code)

	result = __generate_report_data(systems, report_type, start_timestamp, end_timestamp)

	return Utils.json_response(result)

@permission_required()
def report_pdf_view(request, system_code=None):
	start_timestamp = request.POST.get("start_timestamp")
	end_timestamp = request.POST.get("end_timestamp", 0)
	report_type = request.POST.get("report_type")

	if request.is_secure():
		domain_url = "https://" + request.META['HTTP_HOST']
	else:
		domain_url = "http://" + request.META['HTTP_HOST']
	request_url = domain_url + reverse('generate_report_pdf', kwargs={
		'system_code': system_code,
		'report_type': report_type,
		'start_timestamp': start_timestamp,
		'end_timestamp': end_timestamp,
	})

	report_pdf_name = datetime.datetime.now().strftime("%Y%m%d")
	report_pdf_name += "-" + uuid.uuid4().hex[:10] + ".pdf"
	report_pdf_path = os.path.join(TEMP_MEDIA_DIR, report_pdf_name)
	pdf_options = {
		"javascript-delay": '3000',
		'quiet': '',
		'margin-left': '18mm',
		'page-size': 'A3',
	}
	pdfkit.from_url(request_url, report_pdf_path, options=pdf_options)

	with open(report_pdf_path, 'rb') as f:
		response = HttpResponse(f.read(), content_type='application/pdf')
	response['Content-Disposition'] = 'attachment; filename="report.pdf"'
	os.remove(report_pdf_path)

	return response

def generate_report_pdf_view(request, system_code, report_type, start_timestamp, end_timestamp):
	systems = System.get_systems_within_root(system_code)
	start_timestamp = int(start_timestamp)
	end_timestamp = int(end_timestamp)

	m = {}
	m['systems'] = systems
	m["report_type"] = report_type
	m["start_timestamp"] = start_timestamp
	m["end_timestamp"] = end_timestamp

	m["report_data"] = escapejs(json.dumps(__generate_report_data(systems, report_type, start_timestamp, end_timestamp)))

	return render_to_response('generate_report_pdf.html', m)
