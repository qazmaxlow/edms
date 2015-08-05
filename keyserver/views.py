import datetime
import json
import pytz

from dateutil.relativedelta import relativedelta
from django.core.context_processors import csrf
from django.shortcuts import render
from django.utils import dateparse
from django.utils import timezone
from django.utils.decorators import method_decorator
from system.models import System
from utils.auth import permission_required_trails
from user.models import USER_ROLE_ADMIN_LEVEL


@permission_required_trails(required_level=USER_ROLE_ADMIN_LEVEL)
def product_key_manage_view(request):

    m = {}
    m.update(csrf(request))

    return render(request, 'list.html', m)