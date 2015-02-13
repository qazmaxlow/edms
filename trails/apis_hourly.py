from rest_framework import viewsets
from audit.models import Trail
from .serializers import HourSerializer
from django.utils.decorators import method_decorator
from utils.auth import permission_required_trails
from user.models import USER_ROLE_ADMIN_LEVEL
from django.utils import timezone

class TrailViewSet(viewsets.ModelViewSet):
    currentYear=timezone.now().year
    currentMonth=timezone.now().month
    queryset = Trail.objects.filter(created_time__year = currentYear, created_time__month = currentMonth)
    serializer_class = HourSerializer
    
    @method_decorator(permission_required_trails(required_level=USER_ROLE_ADMIN_LEVEL))
    def dispatch(self, request, *args, **kwargs):
        return super(TrailViewSet, self).dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        currentYear=timezone.now().year
        currentMonth=timezone.now().month
        listOfTrail=list(Trail.objects.filter(created_time__year = currentYear, created_time__month = currentMonth))
        hourlyCount=[]
        hourlyList=[]
        startHour=0
        for i in range(24):
            hourlyCount.append(0)
        for i in listOfTrail:
            i.created_time=timezone.localtime(i.created_time)
            hourlyCount[i.created_time.hour]+=1
        for i in hourlyCount:
            hourlyList.append({'hour':startHour,'count':i})
            startHour+=1

        return hourlyList