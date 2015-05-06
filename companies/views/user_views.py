from rest_framework import generics, serializers
from rest_framework.views import APIView

from user.models import EntrakUser


class EntrakUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntrakUser


class CompanyAuthenticatedUserView(generics.RetrieveAPIView):
    serializer_class = EntrakUserSerializer

    def get_object(self):
        return self.request.user
