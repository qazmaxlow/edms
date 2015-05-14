import pytz

# from .serializers import DailyElectricityUsageSerializer
from bson.objectid import ObjectId
from datetime import datetime
from datetime import timedelta
from django.db.models import Q
from django.http import Http404
from django.utils import timezone, dateparse
from egauge.manager import SourceManager
from egauge.models import SourceReadingHour
from mongoengine import connection
from rest_framework import viewsets, filters
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from system.models import System
from utils.auth import permission_required
from common import return_error_response

@api_view(['GET'])
@authentication_classes((TokenAuthentication,))
@permission_classes((IsAuthenticated,))
def DailyElectricityUsageDetail(request, api_version, format=None):

    date = request.QUERY_PARAMS.get('date', '')
    system_code = request.QUERY_PARAMS.get('system_code', '')

    systems_info = System.get_systems_info(system_code, request.user.system.code)

    if not systems_info:
        return return_error_response()

    systems = systems_info['systems']

    sources = SourceManager.get_sources(systems[0])
    source_ids = [str(source.id) for source in sources]

    try:
        user_tz = pytz.timezone(systems[0].timezone)
        user_time = user_tz.localize(datetime.strptime(date, '%Y-%m-%d'))
    except ValueError:
        return return_error_response()

    system_time = timezone.now()

    if system_time.astimezone(user_tz).strftime('%Y-%m-%d') == user_time.strftime('%Y-%m-%d'):
        # Generate "TODAY" data up to current time
        query_date_end_dt = system_time.astimezone(timezone.get_default_timezone())
        query_date_start_dt = query_date_end_dt.astimezone(user_tz).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.get_default_timezone())
    else:
        # Generate whole day data
        query_date_end_dt = user_time.astimezone(timezone.get_default_timezone()) + timedelta(days=1) - timedelta(microseconds=1)
        query_date_start_dt = query_date_end_dt.astimezone(user_tz).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.get_default_timezone())

    comparing_to_start_dt = query_date_start_dt - timedelta(days=7)
    comparing_to_end_dt = query_date_end_dt - timedelta(days=7)

    query_date_readings = SourceReadingHour.objects(
        source_id__in=source_ids,
        datetime__gte=query_date_start_dt,
        datetime__lte=query_date_end_dt).sum('value')

    comparing_to_readings = SourceReadingHour.objects(
        source_id__in=source_ids,
        datetime__gte=comparing_to_start_dt,
        datetime__lte=comparing_to_end_dt).sum('value')

    return Response({
        'generated_at' : system_time.astimezone(user_tz),
        'query_date' : {
            'from' : query_date_start_dt.astimezone(user_tz).strftime('%Y-%m-%d %H:%M:%S'),
            'to' : query_date_end_dt.astimezone(user_tz).strftime('%Y-%m-%d %H:%M:%S'),
            'kWh' : round(query_date_readings,4)
        },
        'comparing_to_date' : {
            'from' : comparing_to_start_dt.astimezone(user_tz).strftime('%Y-%m-%d %H:%M:%S'),
            'to' : comparing_to_end_dt.astimezone(user_tz).strftime('%Y-%m-%d %H:%M:%S'),
            'kWh' : round(comparing_to_readings,4)
        },
    })
