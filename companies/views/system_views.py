from rest_framework import generics

from system.models import System

from rest_framework import serializers
from rest_framework.authentication import SessionAuthentication
from rest_framework.decorators import authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from utils.auth import has_permission


class SystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = System
        fields = ('id', 'fullname')


@authentication_classes((SessionAuthentication,))
@permission_classes((IsAuthenticated,))
class CompanySystemList(generics.ListAPIView):
    serializer_class = SystemSerializer

    def get_queryset(self):
        syscode = self.kwargs['system_code']
        systems = System.get_systems_within_root(syscode)

        if not systems or not has_permission(self.request, self.request.user, systems[0]):
            raise PermissionDenied
        else:
            return systems
