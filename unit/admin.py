from django.contrib import admin
from .models import UnitCategory, UnitRate, UnitType

class UnitCategoryAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'order', 'global_rate', 'has_detail_rate', 'city')
    list_editable = ('name', 'order', 'global_rate',)

class UnitRateAdmin(admin.ModelAdmin):
    pass


class UnitTypeAdmin(admin.ModelAdmin):
    pass


admin.site.register(UnitCategory, UnitCategoryAdmin)
admin.site.register(UnitRate, UnitRateAdmin)
admin.site.register(UnitType, UnitTypeAdmin)
