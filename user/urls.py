from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns(
    '',
    url(r'^activate$', views.activate_account, name='users.activate_account'),
    url(r'^update$', views.update_account, name='users.update_account'),
    url(r'^send_invitation_email$', views.send_invitation_email, name='users.send_invitation_email'),
    url(r'^patch$', views.UpdateUserView.as_view(), name='users.patch_account'),
    url(r'^destroy$', views.DeleteUserView.as_view(), name='users.disable_account'),
)