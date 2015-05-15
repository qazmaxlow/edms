import re

from rest_framework import generics
from rest_framework import serializers
from rest_framework import validators
from rest_framework.views import APIView
from user.models import EntrakUser
from system.models import System
from user.models import USER_LANGUAGES

PASSWORD_REGEX = re.compile(r'^.*(?=.{8,})(?=.*[A-Za-z]+)(?=.*\d).*$')

class EntrakUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntrakUser


class CompanyAuthenticatedUserView(generics.RetrieveAPIView):

    serializer_class = EntrakUserSerializer

    def get_object(self):
        return self.request.user


class LanguageField(serializers.CharField):

    def to_representation(self, value):
        lang = [item for item in USER_LANGUAGES if item[0] == value]
        if lang:
            return super(LanguageField, self).to_representation(lang[0][1])
        else:
            return super(LanguageField, self).to_representation(USER_LANGUAGES[0][1])


class UserSerializer(serializers.ModelSerializer):

    language = LanguageField(required=False)
    username = serializers.CharField(validators=[validators.UniqueValidator(queryset=EntrakUser.objects.all())])
    new_password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = EntrakUser
        fields = ['id', 'username', 'fullname', 'department', 'language', 'email', 'is_email_verified', 'is_personal_account', 'is_active', 'new_password', 'confirm_password']
        write_only_fields = ['new_password', 'confirm_password']


    def validate(self, data):
        if data['new_password'] and data['confirm_password']:
            if data['password'] != data.pop('confirm_password'):
                raise serializers.ValidationError("Passwords do not match")

            if PASSWORD_REGEX.search(data['password']) is None:
                raise serializers.ValidationError("Password must be at least 8 characters long and contains at least one character and one number")

        return data

class UserListView(generics.ListAPIView):

    serializer_class = UserSerializer

    def get_queryset(self):

        syscode = self.kwargs['system_code']
        sys = System.objects.get(code=syscode)
        syss = System.get_systems_within_root(syscode)

        return EntrakUser.objects.filter(is_active=True, system_id__in=[s.id for s in syss])