import calendar
import json
import datetime
from .utils import Utils
from system.models import System
from unit.models import UnitCategory, UnitRate, KWH_CATEGORY_CODE, CO2_CATEGORY_CODE, MONEY_CATEGORY_CODE
from egauge.manager import SourceManager
from egauge.models import Source

def transform_reading(unit_rate_code, timestamp, val, unit_rates):
	match_units = [unit_rate for unit_rate in unit_rates if (unit_rate.code == unit_rate_code and timestamp >= calendar.timegm(unit_rate.effective_date.utctimetuple()))]
	if match_units:
		target_unit_rate = sorted(match_units, key=lambda unit_rate: unit_rate.effective_date, reverse=True)[0]
	else:
		target_unit_rate = sorted(unit_rates, key=lambda unit_rate: unit_rate.effective_date)[0]

	return val*target_unit_rate.rate

def sum_all_readings(source_readings):
	usage = 0
	for _, readings in source_readings.items():
		for _, val in readings.items():
			usage += val;

	return usage

def grep_system_by_code(systems, code):
	return [system for system in systems if system.code == code][0]

def gen_source_system_mapping(systems, sources):
	result = {}
	for source in sources:
		result[str(source.id)] = grep_system_by_code(systems, source.system_code)

	return result

def transform_source_readings(source_readings, systems, sources, unit_rates, unit_category_code):
	system_source_mapping = gen_source_system_mapping(systems, sources)

	for source_id, readings in source_readings.items():
		unit_rate_code = json.loads(system_source_mapping[source_id].unit_info)[unit_category_code]
		for reading_timestamp, reading_val in readings.items():
			readings[reading_timestamp] = transform_reading(unit_rate_code, reading_timestamp, reading_val, unit_rates)

def transform_source_readings_with_global_rate(source_readings, global_rate):
	for _, readings in source_readings.items():
		for reading_timestamp, reading_val in readings.items():
			readings[reading_timestamp] *= global_rate

def combine_readings_by_timestamp(sources_readings):
	result = {}
	for _, readings in sources_readings.items():
		for timestamp, val in readings.items():
			if timestamp in result:
				result[timestamp] += val
			else:
				result[timestamp] = val

	return result

def calculate_total_baseline_energy_usage(start_dt, end_dt, daily_baselines):
	total_energy = 0

	total_day_diff = (end_dt-start_dt).days
	for day_diff in xrange(0,total_day_diff):
		inspect_dt = start_dt+datetime.timedelta(days=day_diff)
		if daily_baselines:
			target_day = 28 if (inspect_dt.month == 2 and inspect_dt.day == 29) else inspect_dt.day
			energy_usage = daily_baselines[inspect_dt.month]['usages'][target_day]
		else:
			energy_usage = 0

		total_energy += energy_usage

	return total_energy
