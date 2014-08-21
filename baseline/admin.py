from django.contrib import admin
from .models import BaselineUsage

class BaselineUsageAdmin(admin.ModelAdmin):
	list_display = ('system', 'start_dt', 'end_dt', 'usage')

admin.site.register(BaselineUsage, BaselineUsageAdmin)
