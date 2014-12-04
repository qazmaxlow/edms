from django.conf.urls import patterns, url
from . import audit_views


urlpatterns = patterns(
    '',
    url('^audit/trails/$', audit_views.CompanyAuditTrailListView.as_view()),
)
