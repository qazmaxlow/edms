from django.contrib import admin
from .models import CityHoliday, Holiday
from system.models import System

class CityHolidayAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'desc', 'city')
    list_editable = ('date', 'desc', 'city')
    list_filter = ('city', )
    ordering = ('city', 'date')

class HolidayAdmin(admin.ModelAdmin):
    list_display = ('id', 'system', 'date', 'desc')
    list_editable = ('system', 'date', 'desc')
    list_filter = ('system', )
    ordering = ('system', 'date')

    def save_model(self, request, obj, form, change):
        if change:
            obj.save()
        else:
            if request.POST.get('apply_subsystem') == 'on':
                systems = System.get_systems_within_root(obj.system.code)
                Holiday.objects.bulk_create([Holiday(
                    system_id=system.id,
                    date=obj.date,
                    desc=obj.desc
                ) for system in systems])
            else:
                obj.save()

admin.site.register(CityHoliday, CityHolidayAdmin)
admin.site.register(Holiday, HolidayAdmin)
