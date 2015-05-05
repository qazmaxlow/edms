from django.conf.urls import patterns, url, include

from rest_framework import routers

from . import audit_views
from . import report_views
from . import dashboard_views
from . import apis
from . import measure_views, export_views, report_schedule_views
from .views import system_views


router = routers.DefaultRouter()
router.register(r'audit/trails', apis.TrailViewSet)

urlpatterns = patterns(
    '',
    url('^audit/trails/$', audit_views.CompanyAuditTrailsListView.as_view()),
    url(r'^apis/', include(router.urls)),
    url(r'^report/$', report_views.report_view, name='companies.report'),
    url(r'^dashboard/$', dashboard_views.dashboard_view, name='companies.dashboard'),
    url(r'^report/summary/ajax/$', report_views.summary_ajax, name='companies.reports.summary.ajax'),
    url(r'^report/popup-report/$', report_views.popup_report_view, name='companies.reports.popup-report.custom-dates'),
    url(r'^report/popup-report/(?P<year>\d{4})/(?P<month>[a-z]{3})/$', report_views.popup_report_view, name='companies.reports.popup-report'),
    url(r'^report/popup-report/download/$', report_views.download_popup_report_view, name='companies.reports.popup-report.download'),

    url(r'^measures/daily/$', measure_views.DailyMeasureList.as_view(), name='companies.measures.daily'),
    url(r'^measures/up-till-now/$', measure_views.EnergyUsedList.as_view(), name='companies.measures.up-till-now'),
    url(r'^measures/total/$', measure_views.TotalDetail.as_view(), name='companies.measures.total'),
    url(r'^measures/top_three/$', measure_views.TopThreeConsumersList.as_view(), name='companies.measures.top-three'),
    url(r'^measures/last_week_stats/$', measure_views.LastWeekDailyCostList.as_view(), name='companies.measures.last-week-stats'),
    url(r'^export/$', export_views.ExportView.as_view(), name='companies.export'),
    url(r'^export/download/$', export_views.DownloadView.as_view(), name='companies.export.download'),
    url(r'^report-schedule/$', report_schedule_views.ReportScheduleView.as_view(), name='companies.report-schedule'),
    url(r'^report-schedule/create/$', report_schedule_views.CreateReportScheduleView.as_view(), name='companies.report-schedule.create'),
    url(r'^report-schedule/destroy/(?P<pk>[0-9]+)/$', report_schedule_views.ReportScheduleTaskDestoryView.as_view(), name='companies.report-schedule.destroy'),
    url(r'^report-schedule/tasks/$', report_schedule_views.ReportScheduleTaskListView.as_view(), name='companies.report-schedule.tasks'),


    url(r'^systems/company-systems/$', system_views.CompanySystemList.as_view(), name='companies.systems.company-systems'),
)
