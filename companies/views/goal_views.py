from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from baseline.models import BaselineUsage
from system.models import System


class goalTracking(APIView):
    def get(self, request, *args, **kwargs):
        info = {}
        response = Response(info, status=status.HTTP_200_OK)
        return response
