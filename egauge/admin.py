from django import forms
from django.contrib import admin

from .models import StatusMonitor


class StatusMonitorForm(forms.ModelForm):

    class Meta:
        model = StatusMonitor


class StatusMonitorAdmin(admin.ModelAdmin):
    form = StatusMonitorForm


admin.site.register(StatusMonitor, StatusMonitorAdmin)
