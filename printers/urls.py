from django.conf.urls import patterns, include, url

from . import graph_views

urlpatterns = patterns('',
    url(r'^graph/$', graph_views.graph_view,
        name="printers.graph"),
    url(r'^measures/show_with_types/$', graph_views.show_measures_with_types_view),
    url(r'^measures/show/$', graph_views.show_measures_view),
    url(r'^measures/show_highest_and_lowest/$', graph_views.show_highest_and_lowest_view),
    url(r'^measures/show_summary/$', graph_views.show_summary_view),
)