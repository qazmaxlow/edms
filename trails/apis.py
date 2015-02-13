from rest_framework import viewsets
from django.db.models import Count
from django.db import connection
from audit.models import Trail
from .serializers import TrailSerializer
from django.utils.decorators import method_decorator
from utils.auth import permission_required_trails
from user.models import USER_ROLE_ADMIN_LEVEL
from datetime import datetime


class TrailViewSet(viewsets.ModelViewSet):
    queryset = Trail.objects.all()
    serializer_class = TrailSerializer
    
    @method_decorator(permission_required_trails(required_level=USER_ROLE_ADMIN_LEVEL))
    def dispatch(self, request, *args, **kwargs):
        return super(TrailViewSet, self).dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        truncate_date = connection.ops.date_trunc_sql('month', 'created_time')
        qs = Trail.objects.extra({'month':truncate_date})
        report = qs.values('month','user__system__code','user__system__name').annotate(Count('pk')).order_by('-month')[:10000]
        timeLimitMonth=2
        timeLimit=datetime.now().date().year*12+datetime.now().month-timeLimitMonth
        listOfRecord=[]
        for r in report:
            month = r.get('month')
            if (month.year*12+month.month<timeLimit):
                continue
            code = r.get('user__system__code')
            if (code==None):
                continue
            name = r.get('user__system__name')
            count = r.get('pk__count')
            action_count = []
            initial_action = 100
            final_action = 701
            for action in range(initial_action,final_action,100):
                temp_qs = qs
                temp_qs = temp_qs.filter(action_type=action,user__system__code=code)
                counter = 0
                for q in temp_qs:
                    if month==q.month:
                        counter = counter+1
                action_count.append(counter)
            record = {'code':code,'name':name,'count':count,'month':month,'graph_count':action_count[0],'ranking_count':action_count[1],'progress_count':action_count[2],'report_count':action_count[3],'display_count':action_count[4],'alert_count':action_count[5],'printer_count':action_count[6]}
            listOfRecord.append(record)
        return listOfRecord
