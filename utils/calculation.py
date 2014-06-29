import calendar

def transform_reading(source, timestamp, val, unit_category_id, units):
	unit_code = source['units'][str(unit_category_id)]
	match_units = [unit for unit in units if (unit.code == unit_code and timestamp >= calendar.timegm(unit.effective_date.utctimetuple()))]
	target_unit = sorted(match_units, key=lambda unit: unit.effective_date, reverse=True)[0]

	return val*target_unit.rate