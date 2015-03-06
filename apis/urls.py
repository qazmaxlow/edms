from django.conf.urls import patterns, url, include
from rest_framework import routers
from . import apis

urlpatterns = patterns(
    '',
    url(r'^v(?P<api_version>\d+)/electricity/data/daily', apis.DailyElectricityUsageDetail, name='electricity-daily'),
)