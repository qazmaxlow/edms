from rest_framework import viewsets

from audit.models import Trail
from .serializers import TrailSerializer


class TrailViewSet(viewsets.ModelViewSet):
    queryset = Trail.objects.all()
    serializer_class = TrailSerializer
    paginate_by = 30
