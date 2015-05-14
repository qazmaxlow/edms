from rest_framework import generics, serializers
from rest_framework.views import APIView
from user.models import EntrakUser
from system.models import System
from user.models import USER_LANGUAGES


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
    language = LanguageField()
    class Meta:
        model = EntrakUser
        fields = ('id', 'username', 'fullname', 'department', 'language', 'email', 'is_email_verified', 'is_personal_account', 'is_active')


class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer


    def get_queryset(self):

        syscode = self.kwargs['system_code']
        sys = System.objects.get(code=syscode)
        syss = System.get_systems_within_root(syscode)

        return EntrakUser.objects.filter(is_active=True, system_id__in=[s.id for s in syss])