import datetime
import pytz
from functools import wraps
from django.utils.decorators import available_attrs
from django.views.decorators.csrf import csrf_exempt
from mongoengine import connection, NotUniqueError
from .models import Printer, PrinterReadingMin, PrinterReadingHour, \
    PrinterReadingDay, PrinterReadingWeek, PrinterReadingMonth, PrinterReadingYear
from utils.utils import Utils


def api_error(view_func):
    @wraps(view_func, assigned=available_attrs(view_func))
    def _wrapped_view_func(request, *args, **kwargs):
        try:
            response = view_func(request, *args, **kwargs)
            return response
        except Exception as e:
            return Utils.json_response({'errors': [{'message': str(e)}]})

    return _wrapped_view_func


@csrf_exempt
@api_error
def set_paper_count_view(request):
    p_id = request.POST.get('p_id')
    datetime = Utils.utc_dt_from_utc_timestamp(int(request.POST.get('timestamp')))
    total = int(request.POST.get('total'))
    duplex = int(request.POST.get('duplex'))
    one_side = int(request.POST.get('one_side'))
    color = int(request.POST.get('color'))
    b_n_w = int(request.POST.get('b_n_w'))
    papersize_a4 = int(request.POST.get('papersize_a4'))
    papersize_non_a4 = int(request.POST.get('papersize_non_a4'))

    printer_timezone = Printer.objects.select_related('system__timezone').get(p_id=p_id).system.timezone

    paper_reading_hour, created = PrinterReadingHour.objects.get_or_create(p_id=p_id, datetime=datetime, defaults={
        'total': total, 'duplex': duplex, 'one_side': one_side,
        'color': color, 'b_n_w': b_n_w,
        'papersize_a4': papersize_a4, 'papersize_non_a4': papersize_non_a4
    })
    if not created:
        paper_reading_hour.update(set__total=total, set__duplex=duplex,
            set__one_side=one_side, set__color=color, set__b_n_w=b_n_w)

    sum_infos = [
        {'range_type': Utils.RANGE_TYPE_DAY, 'target_collection': 'printer_reading_hour', 'update_class': PrinterReadingDay},
        {'range_type': Utils.RANGE_TYPE_WEEK, 'target_collection': 'printer_reading_day', 'update_class': PrinterReadingWeek},
        {'range_type': Utils.RANGE_TYPE_MONTH, 'target_collection': 'printer_reading_day', 'update_class': PrinterReadingMonth},
        {'range_type': Utils.RANGE_TYPE_YEAR, 'target_collection': 'printer_reading_month', 'update_class': PrinterReadingYear},
    ]

    local_datetime = datetime.astimezone(pytz.timezone(printer_timezone))
    for sum_info in sum_infos:
        start_time, end_time = Utils.get_datetime_range(sum_info['range_type'], local_datetime)

        current_db_conn = connection.get_db()
        result = current_db_conn[sum_info['target_collection']].aggregate([
            {"$match": {
                'p_id': p_id,
                'datetime': {'$gte': start_time, '$lt': end_time}}
            },
            {
                "$group": {
                    "_id": "$p_id",
                    "total": {"$sum": "$total"},
                    "duplex": {"$sum": "$duplex"},
                    "one_side": {"$sum": "$one_side"},
                    "color": {"$sum": "$color"},
                    "b_n_w": {"$sum": "$b_n_w"},
                    'papersize_a4': {"$sum": "$papersize_a4"},
                    'papersize_non_a4': {"$sum": "$papersize_non_a4"},
                }
            }
        ])

        for info in result['result']:
            sum_info['update_class'].objects(
                p_id=info['_id'], datetime=start_time
            ).update_one(set__total=info['total'], set__duplex=info['duplex'],
                set__one_side=info['one_side'], set__color=info['color'],
                         set__b_n_w=info['b_n_w'],
                         set__papersize_a4=info['papersize_a4'],
                         set__papersize_non_a4=info['papersize_non_a4'], upsert=True)

    return Utils.json_response({'success': True})
