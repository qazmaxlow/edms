import calendar

def transform_reading(source, timestamp, val, unit_category_id, units):
	unit_code = source['units'][str(unit_category_id)]
	match_units = [unit for unit in units if (unit.code == unit_code and timestamp >= calendar.timegm(unit.effective_date.utctimetuple()))]
	if match_units:
		target_unit = sorted(match_units, key=lambda unit: unit.effective_date, reverse=True)[0]
	else:
		target_unit = sorted(units, key=lambda unit: unit.effective_date)[0]

	return val*target_unit.rate

def sum_all_readings(source_readings):
	usage = 0
	for _, readings in source_readings.items():
		for _, val in readings.items():
			usage += val;

	return usage
