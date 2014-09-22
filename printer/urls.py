from django.conf.urls import patterns, include, url

urlpatterns = patterns('',
	url(r'^set_paper_count/$', 'printer.views.set_paper_count_view', name='set_paper_count'),
)
