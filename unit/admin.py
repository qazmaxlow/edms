from django.contrib import admin
from .models import UnitCategory, UnitRate, UnitType

class UnitCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'order', 'global_rate', 'has_detail_rate', 'city')
    list_editable = ('name', 'order', 'global_rate',)

class UnitRateAdmin(admin.ModelAdmin):
    list_display = ('category_code', 'code', 'rate', 'effective_date')
    list_editable = ('code', 'rate', 'effective_date')
    ordering = ('category_code', 'effective_date')

class UnitTypeAdmin(admin.ModelAdmin):
    pass

admin.site.register(UnitCategory, UnitCategoryAdmin)
admin.site.register(UnitRate, UnitRateAdmin)
admin.site.register(UnitType, UnitTypeAdmin)
