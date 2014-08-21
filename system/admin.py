from django.contrib import admin
from .models import System, SystemHomeImage

class SystemAdmin(admin.ModelAdmin):
	list_display = ('code', 'name', 'path', 'city')

class SystemHomeImageAdmin(admin.ModelAdmin):
	pass

admin.site.register(System, SystemAdmin)
admin.site.register(SystemHomeImage, SystemHomeImageAdmin)
