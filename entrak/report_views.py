import pytz
import datetime
import copy
from django.shortcuts import render_to_response
from django.db.models import Q
from system.models import System, BaselineUsage, UnitRate, CO2_CATEGORY_CODE, MONEY_CATEGORY_CODE
from egauge.manager import SourceManager
from egauge.models import SourceReadingMonth
from utils.auth import permission_required
from utils.utils import Utils
from utils import calculation

@permission_required
def report_view(request, system_code=None):
	systems_info = System.get_systems_info(system_code, request.user.system.code)
	systems = systems_info['systems']
	current_system = systems[0]
	sources = SourceManager.get_sources(current_system)

	current_system_tz = pytz.timezone(current_system.timezone)
	first_record = min([source.first_record for source in sources])
	first_record = current_system_tz.localize(first_record).replace(
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
		monthly_summary.append({'timestamp': timestamp, 'energy_usage': usage,
			'co2_usage': co2_usages[timestamp], 'money_usage': money_usages[timestamp]})

	m = systems_info
	m["monthly_summary"] = sorted(monthly_summary, key=lambda x: x['timestamp'])

	return render_to_response('report.html', m)
