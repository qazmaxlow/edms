import datetime
import pytz
import calendar
import json
from django.shortcuts import render_to_response
from system.models import System, BaselineUsage, UnitRate
from utils.auth import permission_required
from utils.utils import Utils
from egauge.manager import SourceManager
from egauge.models import SourceReadingMonth
from utils import calculation
from settings import CO2_CATEGORY_ID, MONEY_CATEGORY_ID

def assign_source_under_system(systems, sources):
	result = {}
	for system in systems:
		match_sources = [source for source in sources if source.system_code == system.code]
		if match_sources:
			result[system] = match_sources

	return result

def get_last_12_month_co2_consumption(unit_code, unit_rates, source, readings, current_dt):
	source_tz = pytz.timezone(source.tz)
	end_dt = current_dt.astimezone(source_tz)
	end_dt = end_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
	target_readings = readings[str(source.id)]

	co2_consumption = 0
	for month_diff in xrange(12):
		target_dt = Utils.add_month(end_dt, -month_diff)
		timestamp = calendar.timegm(target_dt.utctimetuple())
		energy_usage = target_readings.get(timestamp, 0)
		co2_consumption += calculation.transform_reading(unit_code, timestamp,
			energy_usage, CO2_CATEGORY_ID, unit_rates)

	return co2_consumption

def calulcate_accumulated_saving(co2_unit_code, money_unit_code, unit_rates, baselines, source, readings, current_dt):
	source_tz = pytz.timezone(source.tz)
	start_dt = pytz.utc.localize(source.first_record).astimezone(source_tz)
	if start_dt.day != 1:
		# skip the incomplete month
		start_dt = start_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
		start_dt = Utils.add_month(start_dt, 1)
	else:
		start_dt = start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
	end_dt = current_dt.astimezone(source_tz).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

	target_readings = readings[str(source.id)]

	total_co2_saving = 0
	total_money_saving = 0

	target_dt = start_dt
	while target_dt <= end_dt:
		timestamp = calendar.timegm(target_dt.utctimetuple())
		energy_usage = target_readings.get(timestamp, 0)
		baseline_usage = baselines[target_dt.month]['usage']
		usage_diff = baseline_usage - energy_usage

		total_co2_saving += calculation.transform_reading(co2_unit_code, timestamp,
			usage_diff, CO2_CATEGORY_ID, unit_rates)
		total_money_saving += calculation.transform_reading(money_unit_code, timestamp,
			usage_diff, MONEY_CATEGORY_ID, unit_rates)

		target_dt = Utils.add_month(target_dt, 1)

	return {'co2': total_co2_saving, 'money': total_money_saving}

@permission_required
def progress_view(request, system_code=None):
	systems_info = System.get_systems_info(system_code, request.user.system.code)

	current_system = systems_info['systems'][0]
	sources = SourceManager.get_sources(current_system)
	need_calculate_systems = assign_source_under_system(systems_info['systems'], sources)

	grouped_baselines = BaselineUsage.get_baselines_for_systems([system.id for system in need_calculate_systems.keys()])

	current_dt = pytz.utc.localize(datetime.datetime.now())

	monthly_source_readings = SourceReadingMonth.objects(source_id__in=[str(source.id) for source in sources])
	grouped_monthly_readings = SourceManager.group_readings_with_source_id(monthly_source_readings)

	unit_rates = UnitRate.objects.select_related('unit').filter(unit__category_id=CO2_CATEGORY_ID)

	total_baseline_co2_consumption = 0
	last_12_months_co2_consumption = 0
	total_co2_saving = 0
	total_money_saving = 0
	for system, attached_sources in need_calculate_systems.items():
		baselines = grouped_baselines[system.id]
		baseline_monthly_usages = BaselineUsage.transform_to_monthly_usages(baselines, pytz.timezone(system.timezone))

		unit_info = json.loads(system.unit_info)
		co2_unit_code = unit_info[str(CO2_CATEGORY_ID)]
		money_unit_code = unit_info[str(MONEY_CATEGORY_ID)]

		baseline_co2_consumption = 0
		for month, month_info in baseline_monthly_usages.items():
			timestamp = calendar.timegm(month_info['dt'].utctimetuple())
			baseline_co2_consumption += calculation.transform_reading(co2_unit_code, timestamp,
				month_info['usage'], CO2_CATEGORY_ID, unit_rates)
		total_baseline_co2_consumption += baseline_co2_consumption

		for source in attached_sources:
			co2_consumption = get_last_12_month_co2_consumption(co2_unit_code, unit_rates,
				source, grouped_monthly_readings, current_dt)
			last_12_months_co2_consumption += co2_consumption

			savings = calulcate_accumulated_saving(co2_unit_code, money_unit_code,
				unit_rates, baseline_monthly_usages, source, grouped_monthly_readings, current_dt)
			total_co2_saving += savings['co2']
			total_money_saving += savings['money']
			print total_co2_saving, total_money_saving

	m = systems_info
	m['percengate_change'] = (last_12_months_co2_consumption-total_baseline_co2_consumption)/total_baseline_co2_consumption*100.0
	m['last_12_months_co2_consumption'] = int(last_12_months_co2_consumption/1000)
	m['total_co2_saving'] = int(total_co2_saving/1000)
	m['total_money_saving'] = total_money_saving

	return render_to_response('progress.html', m)
