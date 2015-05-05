from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns(
    '',
    url(r'^activate$', views.activate_account, name='users.activate_account'),
)
