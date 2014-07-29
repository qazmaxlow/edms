import sys
import pytz
import datetime
import copy
import json
import operator
from django.shortcuts import render_to_response
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Q
from mongoengine import Q as MongoQ
from system.models import System
from unit.models import UnitRate, CO2_CATEGORY_CODE, MONEY_CATEGORY_CODE
from baseline.models import BaselineUsage
from egauge.manager import SourceManager
from egauge.models import SourceReadingMonth, SourceReadingDay
from utils.auth import permission_required
from utils.utils import Utils
from utils import calculation

@permission_required
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

	return render_to_response('report.html', m)

def __calculcate_total_max_min(readings, timezone):
	total_val = 0
	max_usage_val = 0
	max_usage_date = None
	min_usage_val = sys.float_info.max
	min_usage_date = None
	for timestamp, val in readings.items():
		dt = Utils.utc_dt_from_utc_timestamp(timestamp).astimezone(timezone)
		total_val += val
		if val > max_usage_val:
			max_usage_val = val;
			max_usage_date = dt.date()

		if val < min_usage_val:
			min_usage_val = val;
			min_usage_date = dt.date()

	if max_usage_date is None:
		max_usage_val = None
	else:
		max_usage_date = max_usage_date.strftime("%Y-%m-%d")
	if min_usage_date is None:
		min_usage_date = None
	else:
		min_usage_date = min_usage_date.strftime("%Y-%m-%d")

	return {
		'total': total_val,
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

def __calculate_overnight_info(readings, timezone, night_time_start, night_time_end):
	filterd_readings = {}
	for timestamp, val in readings.items():
		dt = Utils.utc_dt_from_utc_timestamp(timestamp).astimezone(timezone)
		if dt.time() >= night_time_start and dt.time() < night_time_end:
			filterd_readings[timestamp] = val

	return __calculcate_total_max_min(filterd_readings, timezone)

@permission_required
def report_data_view(request, system_code=None):
	start_dt_timestamp = int(request.POST.get('start_dt'))
	start_dt = Utils.utc_dt_from_utc_timestamp(start_dt_timestamp)
	end_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('end_dt')))
	beginning_start_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('beginning_start_dt')))
	beginning_end_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('beginning_end_dt')))
	last_same_period_start_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('last_same_period_start_dt')))
	last_same_period_end_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('last_same_period_end_dt')))
	last_start_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('last_start_dt')))
	last_end_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('last_end_dt')))

	systems = System.get_systems_within_root(system_code)
	current_system = systems[0]
	sources = SourceManager.get_sources(current_system)

	source_ids = [str(source.id) for source in sources]
	timestamp_info = {
		'currentReadings': {'start': start_dt, 'end': end_dt},
		'beginningReadings': {'start': beginning_start_dt, 'end': beginning_end_dt},
	}
	if last_same_period_start_dt >= current_system.first_record:
		timestamp_info['lastSamePeriodReadings'] = {'start': last_same_period_start_dt, 'end': last_same_period_end_dt}
	if last_start_dt >= current_system.first_record:
		timestamp_info['lastReadings'] = {'start': last_start_dt, 'end': last_end_dt}
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
		for source_id in info["sourceIds"]:
			source_group_map[source_id] = group_idx

			info["currentReadings"] = {}
			info["lastReadings"] = {}
			info["beginningReadings"] = {}
			info["lastSamePeriodReadings"] = {}

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
						target_info["currentTotalEnergy"] = val + target_info.get("currentTotalEnergy", 0)
						target_info["currentTotalCo2"] = calculation.transform_reading(
							co2_unit_rate_code, timestamp, val, co2_unit_rates) + target_info.get("currentTotalCo2", 0)
						target_info["currentTotalMoney"] = calculation.transform_reading(
							money_unit_rate_code, timestamp, val, money_unit_rates) + target_info.get("currentTotalMoney", 0)

	total_energy = 0 
	all_holidays = current_system.get_all_holidays(timestamp_info)
	current_system_timezone = pytz.timezone(current_system.timezone)
	for info in grouped_source_infos:
		total_energy += info['currentTotalEnergy']
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
			info[cal_info['keyPrefix']+'OvernighInfo'] = __calculate_overnight_info(info[cal_info["targetReadings"]],
				current_system_timezone, current_system.night_time_start, current_system.night_time_end)

	total_baseline_energy = 0
	need_calculate_systems = System.assign_source_under_system(systems, sources)
	grouped_baselines = BaselineUsage.get_baselines_for_systems([system.id for system in need_calculate_systems.keys()])
	for system, attached_sources in need_calculate_systems.items():
		system_timezone = pytz.timezone(system.timezone)

		baselines = grouped_baselines[system.id]
		baseline_daily_usages = BaselineUsage.transform_to_daily_usages(baselines, system_timezone)
		total_baseline_energy += calculation.calculate_total_baseline_energy_usage(
			start_dt.astimezone(system_timezone), end_dt.astimezone(system_timezone), baseline_daily_usages)

	saving_info = {}
	unit_info = json.loads(current_system.unit_info)
	co2_unit_code = unit_info[CO2_CATEGORY_CODE]
	money_unit_code = unit_info[MONEY_CATEGORY_CODE]
	energy_saving = total_baseline_energy-total_energy
	saving_info["energy"] = energy_saving/total_baseline_energy*100
	saving_info["co2"] = calculation.transform_reading(co2_unit_code, start_dt_timestamp, energy_saving, co2_unit_rates)
	saving_info["money"] = calculation.transform_reading(money_unit_code, start_dt_timestamp, energy_saving, money_unit_rates)

	result = {}
	result['savingInfo'] = saving_info
	result['holidays'] = [holiday.strftime("%Y-%m-%d") for holiday in all_holidays]

	for info in grouped_source_infos:
		for will_remove_data in ['beginningReadings', 'lastSamePeriodReadings']:
			info.pop(will_remove_data, None)
	result['groupedSourceInfos'] = grouped_source_infos

	return Utils.json_response(result)
