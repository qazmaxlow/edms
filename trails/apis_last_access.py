from rest_framework import viewsets
from django.db.models import Q
from django.db.models import Max
from audit.models import Trail
from .serializers import LastAccessSerializer
from django.utils.decorators import method_decorator
from utils.auth import permission_required_trails
from user.models import USER_ROLE_ADMIN_LEVEL

class TrailViewSet(viewsets.ModelViewSet):
    queryset = Trail.objects.values('user__system__code','user__system__name').filter(~Q(user__system__code = None)).annotate(Max('created_time')).order_by('user__system__code')
    serializer_class = LastAccessSerializer
    
    @method_decorator(permission_required_trails(required_level=USER_ROLE_ADMIN_LEVEL))
    def dispatch(self, request, *args, **kwargs):
        return super(TrailViewSet, self).dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        last_access_qs=Trail.objects.values('user__system__code','user__system__name').filter(~Q(user__system__code = None)).annotate(Max('created_time')).order_by('user__system__code')
        return last_access_qs
