from django.conf.urls import patterns, url, include

from rest_framework import routers

from . import audit_views
from . import report_views
from . import dashboard_views
from . import apis
from . import measure_views


router = routers.DefaultRouter()
router.register(r'audit/trails', apis.TrailViewSet)

urlpatterns = patterns(
    '',
    url('^audit/trails/$', audit_views.CompanyAuditTrailsListView.as_view()),
    url(r'^apis/', include(router.urls)),
    url(r'^report/$', report_views.report_view, name='report'),
    url(r'^dashboard/$', dashboard_views.dashboard_view, name='dashboard'),
    url(r'^report/summary/ajax/$', report_views.summary_ajax, name='companies.reports.summary.ajax'),
    url(r'^report/popup-report/$', report_views.popup_report_view, name='companies.reports.popup-report.custom-dates'),
    url(r'^report/popup-report/(?P<year>\d{4})/(?P<month>[a-z]{3})/$', report_views.popup_report_view, name='companies.reports.popup-report'),
    url(r'^report/popup-report/download/$', report_views.download_popup_report_view, name='companies.reports.popup-report.download'),

    url('^measures/daily/$', measure_views.DailyMeasureList.as_view(), name='companies.measures.daily')
)
