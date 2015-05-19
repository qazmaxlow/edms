from rest_framework import generics

from system.models import System

from rest_framework import serializers


class SystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = System
        fields = ('id', 'fullname')


class CompanySystemList(generics.ListAPIView):
    serializer_class = SystemSerializer

    def get_queryset(self):
        syscode = self.kwargs['system_code']
        systems = System.get_systems_within_root(syscode)
        user_systems = System.get_systems_within_root(self.request.user.system.code)
        qs = user_systems
        return qs
