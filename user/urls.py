from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns(
    '',
    url(r'^activate$', views.activate_account, name='users.activate_account'),
    url(r'^update$', views.update_account, name='users.update_account'),
)
