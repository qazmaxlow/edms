import pytz

# from .serializers import DailyElectricityUsageSerializer
from bson.objectid import ObjectId
from datetime import datetime
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404
from django.utils import timezone, dateparse
from egauge.manager import SourceManager
from egauge.models import SourceReadingHour
from mongoengine import connection
from rest_framework import viewsets, filters
from rest_framework import generics
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from system.models import System
from user.models import EntrakUser
from alert.models import Alert, AlertHistory
from utils.auth import has_permission
from common import return_error_response
from serializers import SystemSerializer, AlertHistorySerializer, RegisterDeviceSerializer


@api_view(['GET'])
@authentication_classes((TokenAuthentication,SessionAuthentication,))
@permission_classes((IsAuthenticated,))
def DailyElectricityUsageDetail(request, api_version, format=None):

    date = request.QUERY_PARAMS.get('date', '')
    system_code = request.QUERY_PARAMS.get('system_code', "")

    systems = System.objects.filter(code=system_code)

    if not systems:
        return return_error_response()
    else:
        system = systems[0]

    if not has_permission(request, request.user, system):
        return return_error_response()

    source_ids = [str(source.id) for source in system.sources]

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


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = 'per_page'
    max_page_size = 100


class SystemListView(generics.ListAPIView):

    serializer_class = SystemSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):

        current_user = self.request.user
        system = current_user.system

        return [system]


class AlertHistoryListView(generics.ListAPIView):

    serializer_class = AlertHistorySerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):

        syscode = self.kwargs['system_code']
        sys = System.objects.get(code=syscode)
        alert_ids = Alert.objects.filter(system_id=sys.id).only('id')
        return AlertHistory.objects.filter(alert_id__in=alert_ids)


class RegisterDeviceView(generics.UpdateAPIView):

    serializer_class = RegisterDeviceSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'user_id'
    lookup_url_kwarg = 'user_id'

    def put(self, request, *args, **kwargs):

        user = EntrakUser.objects.get(username=self.kwargs['username'])
        current_user = request.user

        if user and current_user and user.id == current_user.id:

            user.device_id = request.data.get('device_id', None)
            user.device_type = request.data.get('device_type', None)

            serializer = RegisterDeviceSerializer(user, data=request.data)
            serializer.is_valid(raise_exception=True)
            return Response(serializer.data)

        else:

            return return_error_response()