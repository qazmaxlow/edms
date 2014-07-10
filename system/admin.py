from django.contrib import admin
from .models import SystemHomeImage

class SystemHomeImageAdmin(admin.ModelAdmin):
    pass
admin.site.register(SystemHomeImage, SystemHomeImageAdmin)
