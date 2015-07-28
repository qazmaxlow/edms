from django.conf.urls import patterns, url, include

from rest_framework import routers

from . import audit_views
from . import report_views
from . import report_revamp_views
from . import dashboard_views
from . import apis
from . import measure_views, export_views, report_schedule_views
from .views import system_views, user_views, progress_views, saving_views, goal_views


router = routers.DefaultRouter()
router.register(r'audit/trails', apis.TrailViewSet)

urlpatterns = patterns(
    '',
    url('^audit/trails/$', audit_views.CompanyAuditTrailsListView.as_view()),
    url(r'^apis/', include(router.urls)),
    url(r'^report/$', report_views.report_view, name='companies.report'),
    url(r'^report/revamp$', report_revamp_views.report_view, name='companies.report_revamp'),
    url(r'^dashboard/$', dashboard_views.dashboard_view, name='companies.dashboard'),
    url(r'^report/summary/ajax/$', report_views.summary_ajax, name='companies.reports.summary.ajax'),
    url(r'^report/revamp/summary/ajax/$', report_revamp_views.summary_ajax, name='companies.report_revamp.summary.ajax'),
    url(r'^report/popup-report/$', report_views.popup_report_view, name='companies.reports.popup-report.custom-dates'),
    url(r'^report/revamp/popup-report/$', report_revamp_views.popup_report_view, name='companies.report_revamp.popup-report.custom-dates'),
    url(r'^report/popup-report/(?P<year>\d{4})/(?P<month>[a-z]{3})/$', report_views.popup_report_view, name='companies.reports.popup-report'),
    url(r'^report/popup-report/download/$', report_views.download_popup_report_view, name='companies.reports.popup-report.download'),
    url(r'^report/share-report/download/$', report_views.download_share_report_view, name='companies.reports.share-report.download'),
    url(r'^report/revamp/popup-report/download/$', report_revamp_views.download_popup_report_view, name='companies.report_revamp.popup-report.download'),
    url(r'^report/revamp/share-report/download/$', report_revamp_views.download_share_report_view, name='companies.report_revamp.share-report.download'),
    url(r'^measures/daily/$', measure_views.DailyMeasureList.as_view(), name='companies.measures.daily'),
    url(r'^measures/up-till-now/$', measure_views.EnergyUsedList.as_view(), name='companies.measures.up-till-now'),
    url(r'^measures/total/$', measure_views.TotalDetail.as_view(), name='companies.measures.total'),
    url(r'^measures/top_three/$', measure_views.TopThreeConsumersList.as_view(), name='companies.measures.top-three'),
    url(r'^measures/last_week_stats/$', measure_views.LastWeekDailyCostList.as_view(), name='companies.measures.last-week-stats'),
    url(r'^progresses/so-far-this-year/$', progress_views.progressSoFarThisYear.as_view(), name='companies.progesses.so-far-this-year'),
    url(r'^progresses/compare-to-baseline/$', progress_views.progressCompareToBaseline.as_view(), name='companies.progesses.compare-to-baseline'),
    url(r'^goal/tracking/$', goal_views.goalTracking.as_view(), name='companies.goal.tracking'),
    url(r'^savings/so-far-this-year/$', saving_views.savingSoFarThisYear.as_view(), name='companies.savings.so-far-this-year'),
    url(r'^savings/compare-to-baseline/$', saving_views.compareToBaseline.as_view(), name='companies.savings.compare-to-baseline'),
    url(r'^export/$', export_views.ExportView.as_view(), name='companies.export'),
    url(r'^export/download/$', export_views.DownloadView.as_view(), name='companies.export.download'),
    url(r'^report-schedule/$', report_schedule_views.ReportScheduleView.as_view(), name='companies.report-schedule'),
    url(r'^report-schedule/create/$', report_schedule_views.CreateReportScheduleView.as_view(), name='companies.report-schedule.create'),
    url(r'^report-schedule/update/(?P<pk>[0-9]+)/$', report_schedule_views.ReportScheduleTaskUpdateView.as_view(), name='companies.report-schedule.update'),
    url(r'^report-schedule/destroy/(?P<pk>[0-9]+)/$', report_schedule_views.ReportScheduleTaskDestoryView.as_view(), name='companies.report-schedule.destroy'),
    url(r'^report-schedule/tasks/$', report_schedule_views.ReportScheduleTaskListView.as_view(), name='companies.report-schedule.tasks'),
    url(r'^report-schedule/frequencies/$', report_schedule_views.FrequencyList.as_view(), name='companies.report-schedule.frequencies'),
    url(r'^users$', user_views.UserListView.as_view(), name='companies.users'),

    url(r'^systems/company-systems/$', system_views.CompanySystemList.as_view(), name='companies.systems.company-systems'),

    url(r'^users/authenticated-user/$', user_views.CompanyAuthenticatedUserView.as_view(), name='companies.users.authenticated-user'),
    url(r'^report/share-report/$', report_views.share_popup_report_view, name='companies.reports.share-report.custom-dates'),
    url(r'^report/share-report/(?P<year>\d{4})/(?P<month>[a-z]{3})/$', report_views.share_popup_report_view, name='companies.reports.share-report'),
    url(r'^report/revamp/share-report/$', report_revamp_views.share_popup_report_view, name='companies.report_revamp.share-report.custom-dates'),
    url(r'^report/revamp/share-report/(?P<year>\d{4})/(?P<month>[a-z]{3})/$', report_revamp_views.share_popup_report_view, name='companies.report_revamp.share-report'),
)
