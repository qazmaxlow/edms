import calendar
import json

def transform_reading(unit_code, timestamp, val, unit_category_id, unit_rates):
	match_units = [unit_rate for unit_rate in unit_rates if (unit_rate.unit.code == unit_code and timestamp >= calendar.timegm(unit_rate.effective_date.utctimetuple()))]
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

def transform_source_readings(source_readings, systems, sources, unit_rates, unit_category_id):
	system_source_mapping = gen_source_system_mapping(systems, sources)

	for source_id, readings in source_readings.items():
		unit_code = json.loads(system_source_mapping[source_id].unit_info)[str(unit_category_id)]
		for reading_timestamp, reading_val in readings.items():
			readings[reading_timestamp] = transform_reading(unit_code, reading_timestamp, reading_val, unit_category_id, unit_rates)

def combine_readings_by_timestamp(sources_readings):
	result = {}
	for _, readings in sources_readings.items():
		for timestamp, val in readings.items():
			if timestamp in result:
				result[timestamp] += val
			else:
				result[timestamp] = val

	return result
