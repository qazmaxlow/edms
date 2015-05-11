from rest_framework import generics, serializers
from rest_framework.views import APIView
from user.models import EntrakUser
from system.models import System


class EntrakUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntrakUser


class CompanyAuthenticatedUserView(generics.RetrieveAPIView):
    serializer_class = EntrakUserSerializer

    def get_object(self):
        return self.request.user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntrakUser
        fields = ('id', 'fullname', 'department', 'language', 'email', 'is_email_verified', 'is_personal_account')


class UserListView(generics.ListAPIView):
    serializer_class = UserSerializer


    def get_queryset(self):

        syscode = self.kwargs['system_code']
        sys = System.objects.get(code=syscode)
        syss = System.get_systems_within_root(syscode)

        return EntrakUser.objects.filter(is_active=True, system_id__in=[s.id for s in syss])