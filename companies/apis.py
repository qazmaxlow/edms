from rest_framework import viewsets, filters

from audit.models import Trail
from .audit_views import AuditTrailFilter
from .serializers import TrailSerializer


class TrailViewSet(viewsets.ModelViewSet):
    queryset = Trail.objects.all()
    serializer_class = TrailSerializer
    paginate_by = 30
    filter_class = AuditTrailFilter
    filter_backends = (filters.DjangoFilterBackend,)
