from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
    url(r'^measure/$', 'printer.views.measure_view', name='set_paper_count'),
)
