from django.contrib import admin
from .models import Alert, AlertHistory, AlertContact, AlertEmail

class AlertAdmin(admin.ModelAdmin):
	list_display = ('system', 'name', 'type', 'check_weekdays',
		'start_time', 'end_time')

class AlertHistoryAdmin(admin.ModelAdmin):
	list_display = ('alert', 'created', 'resolved')

class AlertContactAdmin(admin.ModelAdmin):
	list_display = ('name', 'email', 'mobile')

class AlertEmailAdmin(admin.ModelAdmin):
	list_display = ('to_address', 'title')

admin.site.register(Alert, AlertAdmin)
admin.site.register(AlertHistory, AlertHistoryAdmin)
admin.site.register(AlertContact, AlertContactAdmin)
admin.site.register(AlertEmail, AlertEmailAdmin)
