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

    def get_queryset(self):
        company_syscode = self.kwargs['system_code']
        trail_queryset = Trail.objects.filter(user__system__code=company_syscode)
        return trail_queryset
