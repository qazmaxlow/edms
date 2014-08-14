from django.conf.urls import patterns, include, url
from django.conf.urls.static import static
from django.contrib.staticfiles import views
from entrak import settings

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'entrak.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^(?P<system_code>[\w\-]+)/', include(patterns('',
    	url(r'^graph/$', 'entrak.graph_views.graph_view', name='graph'),
        url(r'^source_readings/$', 'entrak.graph_views.source_readings_view'),
    	url(r'^highest_lowest_source_readings/$', 'entrak.graph_views.highest_lowest_source_readings_view'),
    	url(r'^summary/$', 'entrak.graph_views.summary_view'),
        url(r'^progress/$', 'entrak.progress_views.progress_view', name='progress'),
        url(r'^ranking/$', 'entrak.ranking_views.ranking_view', name='ranking'),
    	url(r'^ranking_data/$', 'entrak.ranking_views.ranking_data_view', name='ranking_data'),
        url(r'^report/$', 'entrak.report_views.report_view', name='report'),
        url(r'^report_data/$', 'entrak.report_views.report_data_view', name='report_data'),
        url(r'^report_pdf/$', 'entrak.report_views.report_pdf_view', name='report_pdf'),
        url(r'^generate_report_pdf/(?P<report_type>[\w\-]+)/(?P<start_timestamp>\d+)/(?P<end_timestamp>\d+)/$',
            'entrak.report_views.generate_report_pdf_view', name='generate_report_pdf'),
    ))),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += [
        url(r'^media/(?P<path>.*)$', views.serve),
    ]
