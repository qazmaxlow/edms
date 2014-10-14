from django.contrib import admin
from .models import Alert, AlertHistory, AlertEmail

class AlertAdmin(admin.ModelAdmin):
    list_display = ('system', 'type', 'check_weekdays', 'compare_percent',
        'peak_threshold', 'start_time', 'end_time', 'created')
    list_filter = ('system', 'type')
    search_fields = ['system__code']

class AlertHistoryAdmin(admin.ModelAdmin):
    list_display = ('alert', 'created', 'diff_percent', 'resolved', 'resolved_datetime')
    list_filter = ('alert__system', 'alert__type')
    search_fields = ['alert__system__code']

class AlertEmailAdmin(admin.ModelAdmin):
    list_display = ('created', 'recipient', 'title', 'error')

admin.site.register(Alert, AlertAdmin)
admin.site.register(AlertHistory, AlertHistoryAdmin)
admin.site.register(AlertEmail, AlertEmailAdmin)
