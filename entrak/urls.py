from django.conf.urls import patterns, include, url

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
    	url(r'^summary/$', 'entrak.graph_views.summary_view'),
    	url(r'^progress/$', 'entrak.progress_views.progress_view', name='progress'),
    ))),
)
