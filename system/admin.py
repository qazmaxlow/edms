from django.contrib import admin
from django.db import transaction
from django.db.models import Q
from .models import System, SystemHomeImage
from egauge.models import Source

class SystemAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'full_name', 'path', 'city', 'company_type')
    list_editable = ('name', 'full_name', 'company_type')
    search_fields = ['code', 'full_name']

    def save_model(self, request, obj, form, change):
        if not change:
            obj.save()
            return

        original_code = form.initial.get('code')
        original_path = form.initial.get('path')
        new_code = obj.code
        new_path = obj.path
        if original_code == new_code and original_path == new_path:
            obj.save()
        else:
            if not original_path:
                target_path = ',%s,'%original_code
            else:
                target_path = '%s%s,'%(original_path, original_code)

            if not new_path:
                change_to_path = ',%s,'%new_code
            else:
                change_to_path = '%s%s,'%(new_path, new_code)

            sub_systems = System.objects.filter(path__startswith=target_path)

            with transaction.atomic():
                for sub_system in sub_systems:
                    sub_system.path = sub_system.path.replace(target_path, change_to_path)
                    sub_system.save()

                obj.save()

                Source.objects(system_code=original_code).update(set__system_code=new_code, set__system_path=new_path)
                sub_system_sources = Source.objects(system_code__in=[sub_system.code for sub_system in sub_systems])
                for source in sub_system_sources:
                    source.system_path = source.system_path.replace(target_path, change_to_path)
                    source.save()

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['can_append_to_systems'] = System.objects.all()
        return super(SystemAdmin, self).add_view(request, form_url, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        will_change_system = System.objects.get(id=object_id)
        extra_context['can_append_to_systems'] = System.objects.exclude(Q(id=object_id) | Q(path__contains=',%s,'%will_change_system.code))
        return super(SystemAdmin, self).change_view(request, object_id,
            form_url, extra_context=extra_context)

class SystemHomeImageAdmin(admin.ModelAdmin):
    pass

admin.site.register(System, SystemAdmin)
admin.site.register(SystemHomeImage, SystemHomeImageAdmin)
