from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import generics, serializers

from system.models import System


class SystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = System


class SubSystemList(generics.ListAPIView):
    """
    Get systems by parent system id or user id
    """
    serializer_class = SystemSerializer

    def _get(self, request, *args, **kwargs):
        json = {}
        return Response(json)

    def get_queryset(self):
        syscode = self.kwargs['system_code']
        systems = System.objects.filter(code__startswith=syscode).exclude(code=syscode)
        return systems
