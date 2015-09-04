from django.conf.urls import patterns, url, include
from rest_framework import routers
from . import apis
from .views import systems as systems_views
from .views import meters as meter_views

urlpatterns = patterns(
    '',
    url(r'^v(?P<api_version>\d+)/electricity/data/daily', apis.DailyElectricityUsageDetail, name='electricity-daily'),
    url(r'^v(?P<api_version>\d+)/systems/(?P<system_code>[\w-]+)/sub-systems/$', systems_views.SubSystemList.as_view()),
    url(r'^v(?P<api_version>\d+)/systems/(?P<system_code>[\w-]+)/meter-statuses/$', meter_views.MeterStatusList.as_view()),
    url(r'^v(?P<api_version>\d+)/systems/(?P<system_code>[\w-]+)/meter-statuses/$', meter_views.MeterStatusList.as_view()),
    url(r'^v(?P<api_version>\d+)/systems/$', apis.SystemListView.as_view(), name='system-list'),
    url(r'^v(?P<api_version>\d+)/systems/(?P<system_code>[\w-]+)/alert_histories/$', apis.AlertHistoryListView.as_view(), name='alert-list'),
    url(r'^v(?P<api_version>\d+)/users/(?P<username>[\w.%+-]+(@[A-Za-z0-9.-]+\.[A-Za-z]{2,4})?)/register_device/$', apis.RegisterDeviceView.as_view(), name='register-device'),
)
