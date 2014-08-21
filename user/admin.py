from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import forms
from .models import EntrakUser

class EntrakUserCreationForm(UserCreationForm):
	def clean_username(self):
		# Since User.username is unique, this check is redundant,
		# but it sets a nicer error message than the ORM. See #13147.
		username = self.cleaned_data["username"]
		try:
			get_user_model()._default_manager.get(username=username)
		except get_user_model().DoesNotExist:
			return username
		raise forms.ValidationError(self.error_messages['duplicate_username'])

	class Meta(UserCreationForm.Meta):
		model = EntrakUser

class EntrakUserAdmin(UserAdmin):
	UserAdmin.list_display += ('system',)
	list_editable = ('system',)

	add_form = EntrakUserCreationForm

admin.site.register(EntrakUser, EntrakUserAdmin)
