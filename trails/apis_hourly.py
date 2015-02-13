from rest_framework import viewsets
from audit.models import Trail
from .serializers import HourSerializer
from django.utils.decorators import method_decorator
from utils.auth import permission_required_trails
from user.models import USER_ROLE_ADMIN_LEVEL
from django.utils import timezone

class TrailViewSet(viewsets.ModelViewSet):
    queryset = Trail.objects.all()
    serializer_class = HourSerializer
    
    @method_decorator(permission_required_trails(required_level=USER_ROLE_ADMIN_LEVEL))
    def dispatch(self, request, *args, **kwargs):
        return super(TrailViewSet, self).dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        listOfTrail=list(Trail.objects.all())
        hourlyCount=[]
        hourlyList=[]
        startHour=0
        timeLimitMonth=1
        for i in range(24):
            hourlyCount.append(0)
        for i in listOfTrail:
            i.created_time=timezone.localtime(i.created_time)
            iDate=i.created_time.year*12+i.created_time.month
            cDate=timezone.now().year*12+timezone.now().month-timeLimitMonth
            if (iDate>cDate):
                hourlyCount[i.created_time.hour]+=1
        for i in hourlyCount:
            hourlyList.append({'hour':startHour,'count':i})
            startHour+=1

        return hourlyList