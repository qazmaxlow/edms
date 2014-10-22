from django.contrib import admin
from .models import CityHoliday, Holiday

class CityHolidayAdmin(admin.ModelAdmin):
    list_display = ('id', 'date', 'desc', 'city')
    list_editable = ('date', 'desc', 'city')
    list_filter = ('city', )

class HolidayAdmin(admin.ModelAdmin):
    list_display = ('id', 'system', 'date', 'desc')
    list_editable = ('system', 'date', 'desc')
    list_filter = ('system', )

admin.site.register(CityHoliday, CityHolidayAdmin)
admin.site.register(Holiday, HolidayAdmin)
