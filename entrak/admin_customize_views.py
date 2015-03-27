import json
import pytz
import datetime
from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import render_to_response
from django.views.decorators.csrf import ensure_csrf_cookie
from mongoengine import connection
from system.models import System
from egauge.manager import SourceManager
from egauge.models import Source, SourceMember, SourceReadingMinInvalid
from egauge.tasks import force_retrieve_reading
from baseline.models import BaselineUsage
from holiday.models import CityHoliday
from utils.utils import Utils
from bson.objectid import ObjectId

CAN_UPDATE_SOURCE_FIELDS = ['name', 'xml_url', 'system_code', 'system_path', 'd_name', 'd_name_tc', 'order', 'source_members', 'active']

def __is_source_need_update(source, info):
    need_update = False
    for compare_key in CAN_UPDATE_SOURCE_FIELDS:
        if source.__getattribute__(compare_key) != info[compare_key]:
            need_update = True
            break

    return need_update

def __assign_source_info(source, info):
    for info_key in CAN_UPDATE_SOURCE_FIELDS:
        source.__setattr__(info_key, info[info_key])

@user_passes_test(lambda user: user.is_superuser, login_url='/admin/')
@ensure_csrf_cookie
def invalid_readings_view(request):
    current_db_conn = connection.get_db()
    invalid_readings = current_db_conn.source_reading_min_invalid.aggregate([
        {
            "$group": {
                "_id": "$xml_url",
                "count": { "$sum": 1 },
                "oldest": { "$min": "$datetime" },
                "newest": { "$max": "$datetime" },
            }
        },
        { "$sort" : { "count": -1 } }
    ])['result']

    m = {}
    m['invalid_readings'] = [
        {
            'xml_url': invalid_reading['_id'],
            'count': invalid_reading['count'],
            'oldest': (invalid_reading['oldest']).astimezone(pytz.timezone("Asia/Hong_Kong")),
            'newest': (invalid_reading['newest']).astimezone(pytz.timezone("Asia/Hong_Kong")),
        } for invalid_reading in invalid_readings]
    return render_to_response('admin/invalid_readings.html', m)

@user_passes_test(lambda user: user.is_superuser, login_url='/admin/')
def remove_invalid_readings_view(request):
    xml_url = request.POST.get('xml_url')
    SourceReadingMinInvalid.objects(xml_url=xml_url).delete()

    return Utils.json_response({'success': True})

@user_passes_test(lambda user: user.is_superuser, login_url='/admin/')
@ensure_csrf_cookie
def edit_sources_view(request, system_code=None):
    if request.method == 'GET':
        systems = System.get_systems_within_root(system_code)
        sources = SourceManager.get_sources(systems[0])

        for system in systems:
            match_sources = [source for source in sources if source.system_code == system.code]
            system.sources = match_sources

        m = {}
        m['systems'] = systems

        return render_to_response('admin/edit_sources.html', m)
    elif request.method == 'POST':
        source_infos = json.loads(request.POST.get('source_infos'))
        source_ids = [info["source_id"] for info in source_infos if info["source_id"] is not None]
        sources = Source.objects(id__in=source_ids)

        source_id_map = {}
        for source in sources:
            source_id_map[str(source.id)] = source

        will_insert_sources = []

        for info in source_infos:

            if info['system_path'] == '':
                info['system_path'] = None

            try:
                info['order'] = int(info['order'])
            except ValueError, e:
                info['order'] = 1

            source_members = []

            for m in info['source_members']:
                source_member = SourceMember(id=ObjectId(), name=m['name'], xml_url=m['xml_url'], operator=m['operator'])
                source_members.append(source_member)

            info['source_members'] = source_members

            if info['source_id'] is None:
                source = Source(
                    name=info['name'],
                    xml_url=info['xml_url'],
                    system_code=info['system_code'],
                    system_path=info['system_path'],
                    d_name=info['d_name'],
                    d_name_tc=info['d_name_tc'],
                    order=info['order'],
                    active=info['active'])
                if source_members:
                    source.source_members = source_members
                will_insert_sources.append(source)
            else:
                original_source = source_id_map[info['source_id']]
                if __is_source_need_update(original_source, info):
                    __assign_source_info(original_source, info)
                    print(original_source.__dict__)
                    print(type(original_source.source_members))
                    print(type(info['source_members']))
                    original_source.save()

        if will_insert_sources:
            Source.objects.insert(will_insert_sources)

        return Utils.json_response({'success': True})

@user_passes_test(lambda user: user.is_superuser, login_url='/admin/')
def add_multi_baseline_view(request):
    system_id = request.POST.get('system_id')
    system = System.objects.get(id=system_id)
    system_timezone = pytz.timezone(system.timezone)
    will_insert_baselines = []
    for input_idx in xrange(1,13):
        if input_idx == 12:
            start_dt = system_timezone.localize(
                datetime.datetime.strptime(request.POST.get('start_dt_12'), '%m/%d/%Y'))
            end_dt = system_timezone.localize(
                datetime.datetime.strptime(request.POST.get('end_dt_12'), '%m/%d/%Y'))
        else:
            start_dt = system_timezone.localize(
                datetime.datetime.strptime(request.POST.get('start_dt_%d'%input_idx), '%m/%d/%Y'))
            end_dt = system_timezone.localize(
                datetime.datetime.strptime(request.POST.get('start_dt_%d'%(input_idx+1)), '%m/%d/%Y'))
            end_dt -= datetime.timedelta(days=1)

        usage = float(request.POST.get('usage_%d'%input_idx))
        baseline_usage = BaselineUsage(system_id=system_id, start_dt=start_dt, end_dt=end_dt, usage=usage)
        will_insert_baselines.append(baseline_usage)

    BaselineUsage.objects.bulk_create(will_insert_baselines)

    return Utils.json_response({'success': True})

@user_passes_test(lambda user: user.is_superuser, login_url='/admin/')
def import_city_holidays_view(request):
    city = request.POST.get('city')
    holiday_csv = request.FILES.get('csv_file')
    CityHoliday.insert_holidays_with_file(city, holiday_csv)

    return Utils.json_response({'success': True})

@user_passes_test(lambda user: user.is_superuser, login_url='/admin/')
def recap_data_view(request):
    hk_tz = pytz.timezone("Asia/Hong_Kong")
    start_dt = hk_tz.localize(datetime.datetime.strptime(request.POST.get('start_dt'), '%Y/%m/%d %H:%M'))
    end_dt = hk_tz.localize(datetime.datetime.strptime(request.POST.get('end_dt'), '%Y/%m/%d %H:%M'))

    system_code = request.POST.get('system_code')
    systems = System.get_systems_within_root(system_code)
    system_codes = [system.code for system in systems]

    # use thread or celery will have block for other data retrieve task
    # may be there are some max http connections per process?
    force_retrieve_reading.delay(start_dt, end_dt, system_codes)

    return Utils.json_response({'success': True})
