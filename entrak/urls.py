from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib.staticfiles import views
from django.views.generic.base import RedirectView
from entrak import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
	# Examples:
	# url(r'^$', 'entrak.views.home', name='home'),
	# url(r'^blog/', include('blog.urls')),

	url(r'^grappelli/', include('grappelli.urls')),
	url(r'^admin/', include(admin.site.urls)),
	url(r'^edit_sources/(?P<system_code>[\w\-]+)/$', 'entrak.admin_customize_views.edit_sources_view', name='edit_sources'),
	url(r'^add_multi_baseline/$', 'entrak.admin_customize_views.add_multi_baseline_view', name='add_multi_baseline'),
	url(r'^recap_data/$', 'entrak.admin_customize_views.recap_data_view', name='recap_data'),

	url(r'^(?P<system_code>[\w\-]+)/', include(patterns('',
		url(r'^$', RedirectView.as_view(pattern_name='graph'), name='redirect-to-graph'),
		url(r'^graph/$', 'entrak.graph_views.graph_view', name='graph'),
		url(r'^source_readings/$', 'entrak.graph_views.source_readings_view'),
		url(r'^highest_lowest_source_readings/$', 'entrak.graph_views.highest_lowest_source_readings_view'),
		url(r'^summary/$', 'entrak.graph_views.summary_view'),
		url(r'^progress/$', 'entrak.progress_views.progress_view', name='progress'),
		url(r'^progress_data/$', 'entrak.progress_views.progress_data_view', name='progress_data'),
		url(r'^ranking/$', 'entrak.ranking_views.ranking_view', name='ranking'),
		url(r'^ranking_data/$', 'entrak.ranking_views.ranking_data_view', name='ranking_data'),
		url(r'^report/$', 'entrak.report_views.report_view', name='report'),
		url(r'^report_data/$', 'entrak.report_views.report_data_view', name='report_data'),
		url(r'^report_pdf/$', 'entrak.report_views.report_pdf_view', name='report_pdf'),
		url(r'^generate_report_pdf/(?P<report_type>[\w\-]+)/(?P<start_timestamp>\d+)/(?P<end_timestamp>\d+)/$',
			'entrak.report_views.generate_report_pdf_view', name='generate_report_pdf'),
		url(r'^export_data/$', 'entrak.export_data_views.export_data_view', name='export_data'),
		url(r'^login/$', 'entrak.auth_views.login_view', name='login'),
		url(r'^logout/$', 'entrak.auth_views.logout_view', name='logout'),
		url(r'^display/$', 'entrak.display_views.display_view', name='display'),
		url(r'^display_energy_readings/$', 'entrak.display_views.display_energy_readings_view', name='display_energy_readings'),

		url(r'^alert_settings/$', 'entrak.settings_views.alert_settings_view', name='alert_settings'),
		url(r'^set_alert/$', 'entrak.settings_views.set_alert_view', name='set_alert'),
		url(r'^remove_alert/$', 'entrak.settings_views.remove_alert_view', name='remove_alert'),
	))),
)

if settings.DEBUG:
	urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
	urlpatterns += [
		url(r'^media/(?P<path>.*)$', views.serve),
	]
