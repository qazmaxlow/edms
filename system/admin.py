from django.contrib import admin
from django.db import transaction
from .models import System, SystemHomeImage
from egauge.models import Source

class SystemAdmin(admin.ModelAdmin):
	list_display = ('code', 'name', 'full_name', 'path', 'city')
	list_editable = ('name', 'full_name',)

	def save_model(self, request, obj, form, change):
		original_code = form.initial.get('code')
		new_code = obj.code
		if original_code == new_code:
			obj.save()
		else:
			target_path = ',%s,'%original_code
			new_path = ',%s,'%new_code
			sub_systems = System.objects.filter(path__contains=target_path)

			with transaction.atomic():
				for sub_system in sub_systems:
					sub_system.path = sub_system.path.replace(target_path, new_path)
					sub_system.save()

				obj.save()

				Source.objects(system_code=original_code).update(set__system_code=new_code)
				sub_system_sources = Source.objects(system_code__in=[sub_system.code for sub_system in sub_systems])
				for source in sub_system_sources:
					source.system_path = source.system_path.replace(target_path, new_path)
					source.save()

class SystemHomeImageAdmin(admin.ModelAdmin):
	pass

admin.site.register(System, SystemAdmin)
admin.site.register(SystemHomeImage, SystemHomeImageAdmin)
