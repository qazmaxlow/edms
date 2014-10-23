from django.contrib import admin
from .models import BaselineUsage
from system.models import System

class BaselineUsageAdmin(admin.ModelAdmin):
    list_display = ('system', 'start_dt', 'end_dt', 'usage')
    list_editable = ('start_dt', 'end_dt', 'usage')
    list_filter = ('system', )
    search_fields = ['system__code', 'system__full_name']
    ordering = ('system', 'start_dt')

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['all_systems'] = System.objects.all()
        return super(BaselineUsageAdmin, self).changelist_view(request, extra_context)

admin.site.register(BaselineUsage, BaselineUsageAdmin)
