from django.conf.urls import patterns, url, include
from rest_framework import routers
from . import apis
from .views import systems as systems_views

urlpatterns = patterns(
    '',
    url(r'^v(?P<api_version>\d+)/electricity/data/daily', apis.DailyElectricityUsageDetail, name='electricity-daily'),
    url(r'^v(?P<api_version>\d+)/systems/(?P<system_code>[\w-]+)/sub-systems/$', systems_views.SubSystemList.as_view()),
)
