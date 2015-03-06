from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib import admin
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import forms
from rest_framework.authtoken.models import Token
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
    list_display = UserAdmin.list_display + ('label', 'system', 'role_level', 'api_token')
    list_editable = ('label', 'system', 'role_level')

    add_form = EntrakUserCreationForm

    def api_token(self, obj):
        # Example here, you can use any expression.
        return Token.objects.get_or_create(user=obj)[0]

admin.site.register(EntrakUser, EntrakUserAdmin)
