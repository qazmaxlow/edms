from django.contrib import admin
from .models import Alert, AlertHistory, AlertEmail

class AlertAdmin(admin.ModelAdmin):
	list_display = ('system', 'type', 'check_weekdays',
		'start_time', 'end_time', 'created')

class AlertHistoryAdmin(admin.ModelAdmin):
	list_display = ('alert', 'created', 'diff_percent', 'resolved', 'resolved_datetime')

class AlertEmailAdmin(admin.ModelAdmin):
	list_display = ('created', 'recipient', 'title', 'error')

admin.site.register(Alert, AlertAdmin)
admin.site.register(AlertHistory, AlertHistoryAdmin)
admin.site.register(AlertEmail, AlertEmailAdmin)
