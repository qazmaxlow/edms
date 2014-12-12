from rest_framework import viewsets

from audit.models import Trail
from .serializers import TrailSerializer


class TrailViewSet(viewsets.ModelViewSet):
    queryset = Trail.objects.all()
    serializer_class = TrailSerializer
    paginate_by = 30

    def get_queryset(self):
        queryset = Trail.objects.all()
        user = self.request.QUERY_PARAMS.get('user', None)
        if user:
            queryset = queryset.filter(user=user)
        return queryset
