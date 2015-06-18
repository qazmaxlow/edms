from django.conf.urls import patterns, url

from rest_framework import renderers

from .views import MessageList
from .views import ReadMessageView


# message_list = MessageList.as_view({
#     'get': 'list'
# })

urlpatterns = patterns(
    '',
    url('^notifications/messages/$', MessageList.as_view(), name='companies.notifications.messages'),

)
