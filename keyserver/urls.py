from django.conf.urls import patterns, url
from . import views
from . import apis

urlpatterns = patterns(
    '',
    url(r'^manage/$', 'keyserver.views.product_key_manage_view', name='keyserver.manage'),
    url(r'^keys/$', apis.ProductKeyListView.as_view(), name='keyserver.key-list'),
    url(r'^key/generate/$', apis.GenerateKeyView.as_view(), name='keyserver.generate-key'),
    url(r'^key/activate/$', apis.ActivateKeyView.as_view(), name='keyserver.activate-key'),
)
