from django.contrib import admin
from .models import Printer

class PrinterAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'system', 'order')

admin.site.register(Printer, PrinterAdmin)
