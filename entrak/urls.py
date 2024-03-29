from django.conf.urls.i18n import i18n_patterns
from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib.staticfiles import views
from django.views.generic.base import RedirectView
from notifications.views import ReadMessageView
from rest_framework import routers
from entrak import settings

from django.contrib import admin

from system.views import SystemGoalSettingsView
from trails import trails, apis

import user

admin.autodiscover()
router = routers.SimpleRouter()
router.register(r'audit/trails', apis.MonthlySet, base_name='trail')
router.register(r'audit/last_access', apis.LastAccessSet, base_name='last-access')
router.register(r'audit/hourly', apis.HourlySet, base_name='hourly')
urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'entrak.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),
    url('^audit/trails/$', trails.CompanyAuditTrailsListView.as_view()),
    url(r'^apis/', include(router.urls)),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^invalid_readings/$', 'entrak.admin_customize_views.invalid_readings_view', name='invalid_readings'),
    url(r'^remove_invalid_readings/$', 'entrak.admin_customize_views.remove_invalid_readings_view', name='remove_invalid_readings'),
    url(r'^edit_sources/(?P<system_code>[\w\-]+)/$', 'entrak.admin_customize_views.edit_sources_view', name='edit_sources'),
    url(r'^add_multi_baseline/$', 'entrak.admin_customize_views.add_multi_baseline_view', name='add_multi_baseline'),
    url(r'^import_city_holidays/$', 'entrak.admin_customize_views.import_city_holidays_view', name='import_city_holidays'),
    url(r'^recap_data/$', 'entrak.admin_customize_views.recap_data_view', name='recap_data'),
    url(r'^api/1/printers/measure/$', 'printers.views.measure_view', name='set_paper_count'),

    url(r'^i18n/', include('django.conf.urls.i18n')),

    url(r'^login/$', 'entrak.auth_views.centeral_login_view', name='centeral_login'),

    url(r'^(?P<system_code>[\w\-]+)/', include(patterns('',
        #url(r'^$', RedirectView.as_view(pattern_name='graph'), name='redirect-to-graph'),
        url(r'^$', RedirectView.as_view(pattern_name='companies.dashboard'), name='redirect-to-dashboard'),
        url(r'^graph/$', 'entrak.graph_views.graph_view', name='graph'),
        url(r'^source_readings/$', 'entrak.graph_views.source_readings_view'),
        url(r'^highest_lowest_source_readings/$', 'entrak.graph_views.highest_lowest_source_readings_view'),
        url(r'^summary/$', 'entrak.graph_views.summary_view'),
        url(r'^printers/', include('printers.urls')),
        url(r'^progress/$', 'entrak.progress_views.progress_view', name='progress'),
        url(r'^progress_data/$', 'entrak.progress_views.progress_data_view', name='progress_data'),
        url(r'^ranking/$', 'entrak.ranking_views.ranking_view', name='ranking'),
        url(r'^ranking_data/$', 'entrak.ranking_views.ranking_data_view', name='ranking_data'),
        url(r'^old-report/$', 'entrak.report_views.report_view', name='report'),
        url(r'^report_data/$', 'entrak.report_views.report_data_view', name='report_data'),
        url(r'^report_pdf/$', 'entrak.report_views.report_pdf_view', name='report_pdf'),
        url(r'^report/(?P<start_timestamp>\d+)/(?P<end_timestamp>\d+)/(?P<report_type>[\w\-]+)/download/$', 'entrak.report_views.download_report_view', name='entrak.download_report'),
        url(r'^summary-report/(?P<start_timestamp>\d+)/(?P<end_timestamp>\d+)/(?P<report_type>[\w\-]+)/download/$', 'entrak.report_views.download_summary_report_view', name='entrak.download_summary_report'),
        url(r'^generate_report_pdf/(?P<report_type>[\w\-]+)/(?P<start_timestamp>\d+)/(?P<end_timestamp>\d+)/(?P<lang_code>[\w\-]+)/$',
            'entrak.report_views.generate_report_pdf_view', name='generate_report_pdf'),
        url(r'^generate_summary_report_pdf/(?P<report_type>[\w\-]+)/(?P<start_timestamp>\d+)/(?P<end_timestamp>\d+)/(?P<lang_code>[\w\-]+)/$',
            'entrak.report_views.generate_summary_report_pdf_view', name='generate_summary_report_pdf'),
        url(r'^export_data/$', 'entrak.export_data_views.export_data_view', name='export_data'),
        url(r'^login/$', 'entrak.auth_views.login_view', name='login'),
        url(r'^logout/$', 'entrak.auth_views.logout_view', name='logout'),
        url(r'^display/$', 'entrak.display_views.display_view', name='display'),
        url(r'^display_energy_readings/$', 'entrak.display_views.display_energy_readings_view', name='display_energy_readings'),

        url(r'^alert_settings/$', 'entrak.settings_views.alert_settings_view', name='alert_settings'),
        url(r'^set_alert/$', 'entrak.settings_views.set_alert_view', name='set_alert'),
        url(r'^remove_alert/$', 'entrak.settings_views.remove_alert_view', name='remove_alert'),
        url(r'^general_settings/$', 'entrak.settings_views.general_settings_view', name='general_settings'),
        url(r'^manage_accounts/$', 'entrak.settings_views.manage_accounts_view', name='manage_accounts'),
        url(r'^goal_settings/$', SystemGoalSettingsView.as_view(), name='systems.goals.settings'),
        url(r'^profile/$', 'entrak.settings_views.profile_view', name='profile'),
        url(r'^set_user_info/$', 'entrak.settings_views.set_user_info_view', name='set_user_info'),
        url(r'^delete_user/$', 'entrak.settings_views.delete_user_view', name='delete_user'),

        url(r'^faq/$', 'entrak.static_page_views.faq_view', name='faq'),
        url(r'^disclaimer/$', 'entrak.static_page_views.disclaimer_view', name='disclaimer'),
    ))),
    url(r'^(?P<system_code>[\w\-]+)/', include('companies.urls')),
    url(r'^apis/', include('apis.urls')),
    url(r'^(?P<system_code>[\w\-]+)/', include('notifications.urls')),
    url(r'^users/(?P<user_id>\d+)/', include('user.urls')),
    url(r'^users/create_individual_users', user.views.CreateIndividualUserView.as_view(), name='users.create_individual_users'),
    url(r'^users/create_shared_user', user.views.CreateSharedUserView.as_view(), name='users.create_shared_user'),
    url(r'^users/send_password_reset_email', user.views.SendPasswordResetEmailView.as_view(), name='users.send_password_reset_email'),
    url(r'^o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
    url(r'^messages/(?P<message_id>\d+)/read', ReadMessageView.as_view(), name='notifications.read_message'),
    url(r'^product/', include('keyserver.urls')),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', views.serve),
    ]
