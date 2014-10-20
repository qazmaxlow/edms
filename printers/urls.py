from django.conf.urls import patterns, include, url

from . import graph_views

urlpatterns = patterns('',
    url(r'^graph/$', graph_views.graph_view),
    url(r'^show_measures/$', graph_views.show_measures_view),
)
