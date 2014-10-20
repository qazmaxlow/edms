from django.core.context_processors import csrf
from django.db.models import Q
from django.shortcuts import render_to_response
from django.views.decorators.csrf import ensure_csrf_cookie

from utils.auth import permission_required

from egauge.manager import SourceManager
from entrak.settings import STATIC_URL
from system.models import System, CITY_ALL
from unit.models import UnitCategory, UnitRate, KWH_CATEGORY_CODE


@permission_required()
@ensure_csrf_cookie
def graph_view(request, system_code=None):
    systems_info = System.get_systems_info(system_code, request.user.system.code)

    sources = SourceManager.get_sources(systems_info["systems"][0])

    unit_categorys = list(UnitCategory.objects.filter(Q(city=CITY_ALL) | Q(city=systems_info["systems"][0].city)).order_by('order'))

    m = systems_info
    m['STATIC_URL'] = STATIC_URL
    m.update({'sources': sources, 'unit_categorys': unit_categorys})
    m.update(csrf(request))

    return render_to_response('system/printers/graph.html', m)
