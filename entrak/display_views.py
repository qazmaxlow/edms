import pytz
import datetime
import calendar
import json
from django.utils.html import escapejs
from django.shortcuts import render
from django.core.context_processors import csrf
from django.views.decorators.csrf import ensure_csrf_cookie
from mongoengine import Q as MongoQ
from settings import STATIC_URL
from system.models import System
from egauge.models import SourceReadingHour
from egauge.manager import SourceManager
from utils.utils import Utils
from utils.auth import permission_required
from audit.decorators.trail import log_audit_trail
from constants import audits as constants_audits


@log_audit_trail(action_type=constants_audits.ACTION_VIEW_DISPLAY)
@permission_required()
@ensure_csrf_cookie
def display_view(request, system_code=None):
    system = System.objects.get(code=system_code)
    sources = SourceManager.get_sources(system)

    m = {}
    m['system'] = system
    m['source_ids'] = escapejs(json.dumps([str(source.id) for source in sources]))
    m['STATIC_URL'] = STATIC_URL
    m.update(csrf(request))

    return render(request, 'display.html', m)

def display_energy_readings_view(request, system_code=None):
    system = System.objects.get(code=system_code)
    sources = SourceManager.get_sources(system)

    now_end_dt = pytz.utc.localize(datetime.datetime.utcnow()).astimezone(pytz.timezone(system.timezone))
    now_start_dt = now_end_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    last_start_dt = now_start_dt - datetime.timedelta(days=7)
    last_end_dt = last_start_dt + datetime.timedelta(days=1)

    source_readings = SourceReadingHour.objects(
        MongoQ(datetime__gte=now_start_dt, datetime__lt=now_end_dt) | MongoQ(datetime__gte=last_start_dt, datetime__lt=last_end_dt),
        source_id__in=[source.id for source in sources])

    result = {'current': {}, 'last': {}}
    now_start_timestamp = calendar.timegm(now_start_dt.utctimetuple())
    for reading in source_readings:
        dt_key = calendar.timegm(reading.datetime.utctimetuple())
        if dt_key >= now_start_timestamp:
            target_group = result['current']
        else:
            target_group = result['last']

        if dt_key in target_group:
            target_group[dt_key] += reading.value
        else:
            target_group[dt_key] = reading.value

    return Utils.json_response(result)
