from django.conf.urls import patterns, url, include

from rest_framework import routers

from . import audit_views, report_views, apis


router = routers.DefaultRouter()
router.register(r'audit/trails', apis.TrailViewSet)

urlpatterns = patterns(
    '',
    url('^audit/trails/$', audit_views.CompanyAuditTrailsListView.as_view()),
    url(r'^apis/', include(router.urls)),
    url(r'^report/popup-report/(?P<year>\d{4})/(?P<month>[a-z]{3})/$', report_views.popup_report_view, name='companies.reports.popup-report'),
)
