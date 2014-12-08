import calendar
import decimal
import json
import pytz
import datetime
from mongoengine import connection

from django.core.context_processors import csrf
from django.db.models import Q
from django.shortcuts import render_to_response
from django.views.decorators.csrf import ensure_csrf_cookie

from utils.auth import permission_required
from utils.utils import Utils

from printers.models import (PrinterReadingHour, PrinterReadingDay, PrinterReadingWeek, PrinterReadingMonth, PrinterReadingYear)
from egauge.manager import SourceManager
from entrak.settings import STATIC_URL
from system.models import System, CITY_ALL
from unit.models import UnitCategory, UnitRate, KWH_CATEGORY_CODE
from utils import calculation
from audit.decorators.trail import log_audit_trail
from constants import audits as constants_audits


@log_audit_trail(action_type=constants_audits.ACTION_VIEW_PRINTER)
@permission_required()
@ensure_csrf_cookie
def graph_view(request, system_code=None):
    systems_info = System.get_systems_info(system_code, request.user.system.code)

    sources = SourceManager.get_sources(systems_info["systems"][0])

    unit_categorys = list(UnitCategory.printer_units.filter(Q(city=CITY_ALL) | Q(city=systems_info["systems"][0].city)).order_by('order'))

    m = systems_info
    m['STATIC_URL'] = STATIC_URL
    m.update({'sources': sources, 'unit_categorys': unit_categorys})
    m.update(csrf(request))

    return render_to_response('system/printers/graph.html', m)


def show_measures_view(request, system_code):
    range_type = request.POST.get('range_type')
    paper_type = request.POST.get('paper_type')
    if paper_type:
        paper_type = int(paper_type)

    unit_category_code = request.POST.get('unit_category_code')
    has_detail_rate = (request.POST.get('has_detail_rate') == 'true')
    global_rate = float(request.POST.get('global_rate'))
    start_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('start_dt')))
    end_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('end_dt')))

    # only one printer per one system
    system = System.get_systems_within_root(system_code)[0]
    printer = system.printers.first()
    printers_response = [{'name': printer.name}]

    range_type_mapping = {
        # Utils.RANGE_TYPE_HOUR: {'target_class': SourceReadingMin},
        Utils.RANGE_TYPE_DAY: {'target_class': PrinterReadingHour},
        Utils.RANGE_TYPE_WEEK: {'target_class': PrinterReadingDay},
        Utils.RANGE_TYPE_MONTH: {'target_class': PrinterReadingDay},
        Utils.RANGE_TYPE_YEAR: {'target_class': PrinterReadingMonth},
    }
    target_class = range_type_mapping[range_type]['target_class']

    printer_measures = target_class.objects(
        p_id = str(printer.id),
        datetime__gte=start_dt,
        datetime__lte=end_dt
    )

    measure_field = 'total'
    measure_field_map = {
        1: 'color',
        2: 'b_n_w',
        3: 'one_side',
        4: 'duplex',
        5: 'papersize_a4',
        6: 'papersize_non_a4'
    }

    if paper_type:
        measure_field = measure_field_map[paper_type]

    printer_readings = {}
    for printer_measure in printer_measures:
        dt_key = calendar.timegm(printer_measure.datetime.utctimetuple())
        printer_readings[dt_key] = getattr(printer_measure, measure_field)

    # convert to another units
    if unit_category_code != 'paper':
        if has_detail_rate:
            systems = System.get_systems_within_root(system_code)
            sources = Source.objects(id__in=all_source_ids)
            unit_rates = UnitRate.objects.filter(category_code=unit_category_code)

            calculation.transform_source_readings(source_readings, systems, sources, unit_rates, unit_category_code)
        else:
            for timestamp, val in printer_readings.items():
                printer_readings[timestamp] *= global_rate

    printers_response[0]['readings'] = printer_readings
    printers_response[0]['paper_type'] = paper_type

    return Utils.json_response(printers_response)


def show_measures_with_types_view(request, system_code):
    range_type = request.POST.get('range_type')
    paper_type = request.POST.get('paper_type')
    if paper_type:
        paper_type = int(paper_type)

    unit_category_code = request.POST.get('unit_category_code')
    has_detail_rate = (request.POST.get('has_detail_rate') == 'true')
    global_rate = float(request.POST.get('global_rate'))
    start_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('start_dt')))
    end_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('end_dt')))

    # only one printer per one system
    system = System.get_systems_within_root(system_code)[0]
    printer = system.printers.first()
    printers_response = [{'name': printer.name}]

    range_type_mapping = {
        # Utils.RANGE_TYPE_HOUR: {'target_class': SourceReadingMin},
        Utils.RANGE_TYPE_DAY: {'target_class': PrinterReadingHour},
        Utils.RANGE_TYPE_WEEK: {'target_class': PrinterReadingDay},
        Utils.RANGE_TYPE_MONTH: {'target_class': PrinterReadingDay},
        Utils.RANGE_TYPE_YEAR: {'target_class': PrinterReadingMonth},
    }
    target_class = range_type_mapping[range_type]['target_class']

    printer_measures = target_class.objects(
        p_id = str(printer.id),
        datetime__gte=start_dt,
        datetime__lte=end_dt
    )

    measure_field = 'total'
    measure_field_map = {
        1: 'color',
        2: 'b_n_w',
        3: 'one_side',
        4: 'duplex',
        5: 'papersize_a4',
        6: 'papersize_non_a4'
    }

    if paper_type:
        measure_field = measure_field_map[paper_type]

    printer_readings = {}
    for printer_measure in printer_measures:
        dt_key = calendar.timegm(printer_measure.datetime.utctimetuple())
        # printer_readings[dt_key] = getattr(printer_measure, measure_field)
        printer_readings[dt_key] = {
            'total': printer_measure.total, 'color': printer_measure.color,
            'b_n_w': printer_measure.one_side, 'one_side': printer_measure.one_side,
            'duplex': printer_measure.duplex,
            'papersize_a4': printer_measure.papersize_a4, 'papersize_non_a4': printer_measure.papersize_non_a4}

    # convert to another units
    # if unit_category_code != 'paper':
    #     if has_detail_rate:
    #         systems = System.get_systems_within_root(system_code)
    #         sources = Source.objects(id__in=all_source_ids)
    #         unit_rates = UnitRate.objects.filter(category_code=unit_category_code)

    #         calculation.transform_source_readings(source_readings, systems, sources, unit_rates, unit_category_code)
    #     else:
    #         for timestamp, val in printer_readings.items():
    #             printer_readings[timestamp] *= global_rate

    printers_response[0]['readings'] = printer_readings
    printers_response[0]['paper_type'] = paper_type

    return Utils.json_response(printers_response)


def get_readings(printer, range_type, start_dt, end_dt):
    range_type_mapping = {
        Utils.RANGE_TYPE_DAY: {'target_class': PrinterReadingHour},
        Utils.RANGE_TYPE_WEEK: {'target_class': PrinterReadingDay},
        Utils.RANGE_TYPE_MONTH: {'target_class': PrinterReadingDay},
        Utils.RANGE_TYPE_YEAR: {'target_class': PrinterReadingMonth},
    }
    target_class = range_type_mapping[range_type]['target_class']
    readings = target_class.objects(
        p_id=str(printer.id),
        datetime__gte=start_dt,
        datetime__lt=end_dt)
    grouped_readings = {}

    for reading in readings:
        if str(reading.p_id) not in grouped_readings:
            grouped_readings[str(reading.p_id)] = {}

        dt_key = calendar.timegm(reading.datetime.utctimetuple())
        grouped_readings[str(reading.p_id)][dt_key] = reading.total

    return grouped_readings


def get_most_readings(printer, range_type, tz_offset, sort_order, system, start_dt):
    range_type_mapping = {
        Utils.RANGE_TYPE_HOUR: {'compare_collection': 'printer_reading_hour'},
        Utils.RANGE_TYPE_DAY: {'compare_collection': 'printer_reading_day'},
        Utils.RANGE_TYPE_WEEK: {'compare_collection': 'printer_reading_week'},
        Utils.RANGE_TYPE_MONTH: {'compare_collection': 'printer_reading_month'},
        Utils.RANGE_TYPE_YEAR: {'compare_collection': 'printer_reading_year'},
    }

    system_timezone = pytz.timezone(system.timezone)
    dt_lower_bound = system.first_record.astimezone(system_timezone).replace(
            hour=0, minute=0, second=0, microsecond=0)
    dt_upper_bound = pytz.utc.localize(datetime.datetime.utcnow()).astimezone(system_timezone).replace(
        minute=0, second=0, microsecond=0)

    match_condition = {'p_id': str(printer.id)}
    if range_type == Utils.RANGE_TYPE_HOUR:
        match_condition["datetime"] = {'$lt': dt_upper_bound}
    elif range_type == Utils.RANGE_TYPE_DAY:
        dt_upper_bound = dt_upper_bound.replace(hour=0)
        match_condition["datetime"] = {'$lt': dt_upper_bound}
    elif range_type == Utils.RANGE_TYPE_WEEK:
        dt_upper_bound = dt_upper_bound.replace(hour=0)
        dt_upper_bound -= datetime.timedelta(days=(dt_upper_bound.weekday()+1))
        if dt_lower_bound.weekday() != 6:
            dt_lower_bound += datetime.timedelta(days=(6-dt_lower_bound.weekday()))
        match_condition["datetime"] = {'$gte': dt_lower_bound, '$lt': dt_upper_bound}
    elif range_type == Utils.RANGE_TYPE_MONTH:
        dt_upper_bound = dt_upper_bound.replace(day=1, hour=0)
        if dt_lower_bound.day != 1:
            dt_lower_bound = Utils.add_month(dt_lower_bound, 1).replace(day=1)
        match_condition["datetime"] = {'$gte': dt_lower_bound, '$lt': dt_upper_bound}
    elif range_type == Utils.RANGE_TYPE_YEAR:
        dt_upper_bound = dt_upper_bound.replace(month=1, day=1, hour=0)
        if dt_lower_bound.month != 1 or dt_lower_bound.day != 1:
            dt_lower_bound = dt_lower_bound.replace(year=(dt_lower_bound.year+1), month=1, day=1)
        match_condition["datetime"] = {'$gte': dt_lower_bound, '$lt': dt_upper_bound}

    aggregate_pipeline = [
        {"$match": match_condition},
        {
            "$group": {
                "_id": "$datetime",
                "total": {"$sum": "$total"}
            }
        },
        {"$sort": {"total": sort_order}},
    ]

    # lowest need to check data complete or not, cannot limit to 1
    if range_type != Utils.RANGE_TYPE_DAY and sort_order == -1:
        aggregate_pipeline.append({"$limit": 1})

    mapped_info = range_type_mapping[range_type]
    current_db_conn = connection.get_db()
    result = current_db_conn[mapped_info['compare_collection']].aggregate(aggregate_pipeline)

    info = {}

    # only that day of a week, e.g Monday
    if range_type == Utils.RANGE_TYPE_DAY:
        target_weekday = start_dt.astimezone(system_timezone).weekday()
        valid_results = []
        for result_data in result["result"]:
            result_data_dt = result_data["_id"].astimezone(system_timezone)
            if result_data_dt.weekday() == target_weekday:
                valid_results.append(result_data)
        result["result"] = valid_results

    # check if have complete data for lowest
    if sort_order == 1:
        for result_data in result["result"]:
            if is_reading_complete(range_type, printer, result_data["_id"], tz_offset):
                result['result'] = [result_data]
                break

    if result["result"]:
        start_dt = result["result"][0]["_id"].astimezone(pytz.utc)
        end_dt = Utils.gen_end_dt(range_type, start_dt, tz_offset)

        info['timestamp'] = calendar.timegm(start_dt.utctimetuple())
        info['readings'] = get_readings(printer, range_type, start_dt, end_dt)

    else:
        info['timestamp'] = None
        info['readings'] = {}

    return info


def is_reading_complete(range_type, printer, start_dt, tz_offset):
    range_type_mapping = {
        Utils.RANGE_TYPE_HOUR: {'check_collection': 'printer_reading_min', 'complete_count': 60},
        Utils.RANGE_TYPE_DAY: {'check_collection': 'printer_reading_hour', 'complete_count': 24},
        Utils.RANGE_TYPE_WEEK: {'check_collection': 'printer_reading_day', 'complete_count': 7},
        Utils.RANGE_TYPE_MONTH: {'check_collection': 'printer_reading_day', 'complete_count': 28},
        Utils.RANGE_TYPE_YEAR: {'check_collection': 'printer_reading_month', 'complete_count': 12},
    }
    end_dt = Utils.gen_end_dt(range_type, start_dt, tz_offset)

    current_db_conn = connection.get_db()
    mapped_info = range_type_mapping[range_type]
    result = current_db_conn[mapped_info['check_collection']].aggregate([
        {
            "$match": {
                'p_id': str(printer.id),
                'datetime': {'$gte': start_dt, '$lt': end_dt},
            }
        },
        {
            "$group": {"_id": "$datetime"}
        }
    ])

    return len(result["result"]) >= mapped_info['complete_count']


def show_highest_and_lowest_view(request, system_code):
    start_dt = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('start_dt')))
    source_infos = json.loads(request.POST.get('source_infos'))
    range_type = request.POST.get('range_type')
    unit_category_code = request.POST.get('unit_category_code')
    has_detail_rate = (request.POST.get('has_detail_rate') == 'true')
    global_rate = float(request.POST.get('global_rate'))
    tz_offset = int(request.POST.get('tz_offset'))/60
    is_highest = (request.POST.get('is_highest') == "true")
    sort_order = -1 if is_highest else 1
    systems = System.get_systems_within_root(system_code)
    current_system = systems[0]

    printer = current_system.printers.first()
    printers_response = [{'name': printer.name}]

    printer_readings_info = get_most_readings(
        printer,
        range_type, tz_offset,sort_order, current_system, start_dt)
    printer_readings_info['name'] = printer.name

    if unit_category_code != 'paper':
        if has_detail_rate:
            sources = Source.objects(id__in=source_infos['source_ids'])
            unit_rates = UnitRate.objects.filter(category_code=unit_category_code)

            calculation.transform_source_readings(source_readings_info['readings'], systems, sources, unit_rates, unit_category_code)
        else:
            calculation.transform_source_readings_with_global_rate(source_readings_info['readings'], global_rate)

    total_readings = {}
    for _, readings in printer_readings_info['readings'].items():
        for timestamp, val in readings.items():
            if timestamp in total_readings:
                total_readings[timestamp]['total'] += val
            else:
                total_readings[timestamp] = {'total': val}
    printer_readings_info['readings'] = total_readings

    return Utils.json_response(printer_readings_info)


def show_summary_view(request, system_code):
    system = System.get_systems_within_root(system_code)[0]
    printer = system.printers.first()

    start_dt = Utils.utc_dt_from_utc_timestamp(int(decimal.Decimal(request.POST.get('start_dt'))))
    end_dt = Utils.utc_dt_from_utc_timestamp(int(decimal.Decimal(request.POST.get('end_dt'))))
    last_start_dt = Utils.utc_dt_from_utc_timestamp(int(decimal.Decimal(request.POST.get('last_start_dt'))))
    last_end_dt = Utils.utc_dt_from_utc_timestamp(int(decimal.Decimal(request.POST.get('last_end_dt'))))

    printer_readings = get_readings(printer, Utils.RANGE_TYPE_MONTH, start_dt, end_dt)
    usage = calculation.sum_all_readings(printer_readings)

    last_source_readings = get_readings(printer, Utils.RANGE_TYPE_MONTH, last_start_dt, last_end_dt)
    last_usage = calculation.sum_all_readings(last_source_readings)

    return Utils.json_response({'realtime': usage, 'last': last_usage})
