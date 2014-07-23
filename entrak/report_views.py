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
	start_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('start_dt')))
	separate_timestamp = int(request.POST.get('separate_dt'))
	end_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('end_dt')))

	systems = System.get_systems_within_root(system_code)
	current_system = systems[0]
	sources = SourceManager.get_sources(current_system)

	source_ids = [str(source.id) for source in sources]
	source_readings = SourceManager.get_readings_with_target_class(source_ids, SourceReadingDay, start_dt, end_dt)

	grouped_source_infos = []
	for source in sources:
		if source.system_code == system_code:
			grouped_source_infos.append({"system_code": system_code, "source_ids": [str(source.id)]})
		else:
			system_path_components = [code for code in source.system_path.split(',') if code != '']
			system_path_idx = system_path_components.index(system_code)
			if system_path_idx+1 >= len(system_path_components):
				grouped_system_code = source.system_code
			else:
				grouped_system_code = system_path_components[system_path_idx+1]
			match_group_idx = None
			for group_idx, info in enumerate(grouped_source_infos):
				if grouped_system_code == info["system_code"]:
					match_group_idx = group_idx
					break

			if match_group_idx is None:
				grouped_source_infos.append({"system_code": grouped_system_code, "source_ids": [str(source.id)]})
			else:
				grouped_source_infos[match_group_idx]["source_ids"].append(str(source.id))

	source_group_map = {}
	for group_idx, info in enumerate(grouped_source_infos):
		for source_id in info["source_ids"]:
			source_group_map[source_id] = group_idx

			info["source_readings"] = {}
			info["last_source_readings"] = {}

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
			if (timestamp >= separate_timestamp):
				readings_key = "source_readings"
				energy_key = "total_energy"
				co2_key = "total_co2"
				money_key = "total_money"
			else:
				readings_key = "last_source_readings"
				energy_key = "last_total_energy"
				co2_key = "last_total_co2"
				money_key = "last_total_money"
			target_info[readings_key][timestamp] = val + target_info[readings_key].get(timestamp, 0)
			target_info[energy_key] = val + target_info.get(energy_key, 0)
			target_info[co2_key] = calculation.transform_reading(
				co2_unit_rate_code, timestamp, val, co2_unit_rates) + target_info.get(co2_key, 0)
			target_info[money_key] = calculation.transform_reading(
				money_unit_rate_code, timestamp, val, money_unit_rates) + target_info.get(money_key, 0)

	return Utils.json_response({'grouped_source_infos': grouped_source_infos})
