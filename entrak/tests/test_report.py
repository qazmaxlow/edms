from PIL import Image
from StringIO import StringIO
import datetime,pytz,random,json

from django.core.files.base import ContentFile
from django.test import TestCase

from user.models import EntrakUser
from system.models import System,DEFAULT_NIGHT_TIME_START,DEFAULT_NIGHT_TIME_END
from egauge.models import *
from egauge.manager import *
from unit.models import *


class ReportSummaryTestCase(TestCase):
    def setUp(self):  
        user = EntrakUser.objects.create_user('ettester01', 'et01@just.test', '00000')

        logo_file = StringIO()
        logo = Image.new('RGBA', size=(50,50), color=(256,0,0))
        logo.save(logo_file, 'png')
        logo_file.seek(0)

        dlogo_file = ContentFile(logo_file.read(), 'test.png')
        
        UnitRate.objects.create(category_code='money',code='hkec',rate=1.45,effective_date=datetime.datetime.now().replace(year=2014))
        
        infoData = '{"money":"hkec","co2":"hkec"}'
        system = System.objects.create(code='ettestsys01',
                              name='ettestsys01',
                              logo=dlogo_file,
                              first_record=datetime.datetime.now().replace(month=datetime.datetime.now().month-1),
                              unit_info = infoData
        )
        if (Source.objects.filter(name='testSource')):
            sources = Source.objects.get(name='testSource')
            SourceReadingMonth.objects.filter(source_id=sources.id).delete()
            SourceReadingDay.objects.filter(source_id=sources.id).delete()
            SourceReadingHour.objects.filter(source_id=sources.id).delete()
            SourceReadingMin.objects.filter(source_id=sources.id).delete()
        else:
            sources = Source(name='testSource',
                             system_code='ettestsys01',
                             system_name='ettestsys01',
                             d_name='testSource'
                             )
            sources.save()
        testNumber=100
        i=0
        while(i<testNumber):
            testDatetime=datetime.datetime.now().replace(hour=int(random.random()*24),minute=int(random.random()*60),second=0,microsecond=0)
            if (SourceReadingMin.objects.filter(source_id=sources.id,datetime=testDatetime)):
                continue
            srm=SourceReadingMin(source_id=sources.id,
                                 datetime=testDatetime,
                                 value=15*random.random()
                                 )
            srm.save()
            i+=1

        for j in SourceReadingMin.objects.filter(source_id=sources.id):
            if (SourceReadingHour.objects.filter(source_id=sources.id,datetime=j.datetime.replace(minute=0))):
                temp=SourceReadingHour.objects.get(source_id=sources.id,datetime=j.datetime.replace(minute=0))
                temp.value+=j.value
                temp.save()
            else:
                srh=SourceReadingHour(source_id=sources.id,
                                 datetime=j.datetime.replace(minute=0),
                                 value=j.value
                                 )
                srh.save()

        for j in SourceReadingHour.objects.filter(source_id=sources.id):
            if (SourceReadingDay.objects.filter(source_id=sources.id,datetime=j.datetime.replace(hour=0))):
                temp=SourceReadingDay.objects.get(source_id=sources.id,datetime=j.datetime.replace(hour=0))
                temp.value+=j.value
                temp.save()
            else:
                srd=SourceReadingDay(source_id=sources.id,
                                 datetime=j.datetime.replace(hour=0),
                                 value=j.value
                                 )
                srd.save()

        for j in SourceReadingDay.objects.filter(source_id=sources.id):
            if (SourceReadingMonth.objects.filter(source_id=sources.id,datetime=j.datetime.replace(day=1))):
                temp=SourceReadingMonth.objects.get(source_id=sources.id,datetime=j.datetime.replace(day=1))
                temp.value+=j.value
                temp.save()
            else:
                srmonth=SourceReadingMonth(source_id=sources.id,
                                 datetime=j.datetime.replace(day=1),
                                 value=j.value
                                 )
                srmonth.save()
                
        system_tz = pytz.timezone(system.timezone)
        user.system = system
        user.save()

    def test_total_cost(self):
        self.client.post('/ettestsys01/login/', {
            'username': 'ettester01',
            'password': '00000',
        })
        current_date=datetime.datetime.now().date()
        start_date=current_date.replace(day=1).strftime("%Y-%m-%d")
        end_date=current_date.replace(day=calendar.monthrange(current_date.year, current_date.month)[1]).strftime("%Y-%m-%d")
        response = self.client.get('/ettestsys01/report/summary/ajax/?start_date='+start_date+'&end_date='+end_date+'&compare_type=month')
        string = response.content
        json_obj = json.loads(string)
        formated_total_cost_in_ajax = int(json_obj['formated_total_cost'][1:].replace(",", ""))
        actual_source_id = Source.objects.get(name='testSource').id
        actual_total_cost = 0
        for j in SourceReadingMin.objects.filter(source_id=actual_source_id):
            actual_total_cost += j.value
        actual_formated_total_cost = round(actual_total_cost*1.45)
        self.assertEqual(formated_total_cost_in_ajax,actual_formated_total_cost)
        
    def test_weekday_cost(self):
        self.client.post('/ettestsys01/login/', {
            'username': 'ettester01',
            'password': '00000',
        })
        current_date=datetime.datetime.now().date()
        start_date=current_date.replace(day=1).strftime("%Y-%m-%d")
        end_date=current_date.replace(day=calendar.monthrange(current_date.year, current_date.month)[1]).strftime("%Y-%m-%d")
        response = self.client.get('/ettestsys01/report/summary/ajax/?start_date='+start_date+'&end_date='+end_date+'&compare_type=month')
        string = response.content
        json_obj = json.loads(string)
        formated_weekday_cost_in_ajax = int(json_obj['formated_weekday_cost'][1:].replace(",", ""))
        actual_source_id = Source.objects.get(name='testSource').id
        actual_total_cost = 0
        for j in SourceReadingMin.objects.filter(source_id=actual_source_id):
            actual_total_cost += j.value
        actual_formated_weekday_cost = round(actual_total_cost*1.45)
        self.assertEqual(formated_weekday_cost_in_ajax,actual_formated_weekday_cost)
        
    def test_overnight_cost(self):
        self.client.post('/ettestsys01/login/', {
            'username': 'ettester01',
            'password': '00000',
        })
        current_date=datetime.datetime.now().date()
        start_date=current_date.replace(day=1).strftime("%Y-%m-%d")
        end_date=current_date.replace(day=calendar.monthrange(current_date.year, current_date.month)[1]).strftime("%Y-%m-%d")
        response = self.client.get('/ettestsys01/report/summary/ajax/?start_date='+start_date+'&end_date='+end_date+'&compare_type=month')
        string = response.content
        json_obj = json.loads(string)
        print json_obj
        formated_overnight_cost_in_ajax = int(json_obj['formated_overnight_avg_cost'][1:].replace(",", ""))
        actual_source_id = Source.objects.get(name='testSource').id
        actual_total_cost = 0
        for j in SourceReadingMin.objects.filter(source_id=actual_source_id):
            if (j.datetime.time()>DEFAULT_NIGHT_TIME_START or j.datetime.time()<DEFAULT_NIGHT_TIME_END):
                actual_total_cost += j.value
        actual_formated_overnight_cost = round(actual_total_cost*1.45/calendar.monthrange(current_date.year,current_date.month)[1])
        self.assertEqual(formated_overnight_cost_in_ajax,actual_formated_overnight_cost)