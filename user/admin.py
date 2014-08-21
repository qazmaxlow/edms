from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from .models import EntrakUser

class EntrakUserAdmin(UserAdmin):
	UserAdmin.list_display += ('system',)

admin.site.register(EntrakUser, EntrakUserAdmin)
