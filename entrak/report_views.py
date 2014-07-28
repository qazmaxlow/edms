import pytz
import datetime
import copy
import json
from django.shortcuts import render_to_response
from django.views.decorators.csrf import ensure_csrf_cookie
from django.db.models import Q
from system.models import System, BaselineUsage, UnitRate, CO2_CATEGORY_CODE, MONEY_CATEGORY_CODE
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

@permission_required
def report_data_view(request, system_code=None):
	start_dt_timestamp = int(request.POST.get('start_dt'))
	start_dt = Utils.utc_dt_from_utc_timestamp(start_dt_timestamp)
	end_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('end_dt')))

	systems = System.get_systems_within_root(system_code)
	current_system = systems[0]
	sources = SourceManager.get_sources(current_system)

	source_ids = [str(source.id) for source in sources]
	source_readings = SourceManager.get_readings_with_target_class(source_ids, SourceReadingDay, start_dt, end_dt)

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

			info["sourceReadings"] = {}
			info["lastSourceReadings"] = {}

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
			readings_key = "sourceReadings"
			energy_key = "totalEnergy"
			co2_key = "totalCo2"
			money_key = "totalMoney"

			target_info[readings_key][timestamp] = val + target_info[readings_key].get(timestamp, 0)
			target_info[energy_key] = val + target_info.get(energy_key, 0)
			target_info[co2_key] = calculation.transform_reading(
				co2_unit_rate_code, timestamp, val, co2_unit_rates) + target_info.get(co2_key, 0)
			target_info[money_key] = calculation.transform_reading(
				money_unit_rate_code, timestamp, val, money_unit_rates) + target_info.get(money_key, 0)

	total_energy = 0 
	for info in grouped_source_infos:
		total_energy += info['totalEnergy']

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
	print total_baseline_energy, energy_saving
	saving_info["energy"] = energy_saving/total_baseline_energy*100
	saving_info["co2"] = calculation.transform_reading(co2_unit_code, start_dt_timestamp, energy_saving, co2_unit_rates)
	saving_info["money"] = calculation.transform_reading(money_unit_code, start_dt_timestamp, energy_saving, money_unit_rates)

	result = {}
	result['groupedSourceInfos'] = grouped_source_infos
	result['holidays'] = current_system.get_all_holidays(start_dt, end_dt)
	result['savingInfo'] = saving_info

	return Utils.json_response(result)
