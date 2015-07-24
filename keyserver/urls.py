from django.conf.urls import patterns, url
from . import views
from . import apis

urlpatterns = patterns(
    '',
    url(r'^manage/$', views.ProductKeyManageView.as_view(), name='product-key-manage'),
    url(r'^keys/$', apis.ProductKeyListView.as_view(), name='product-key-list'),
)
