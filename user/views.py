import datetime
import json
import pytz

from dateutil.relativedelta import relativedelta
from django.core.context_processors import csrf
from django.shortcuts import render
from django.shortcuts import redirect
from django.utils import dateparse
from django.utils import timezone
from operator import itemgetter
from django.utils.translation import ugettext as _

from egauge.manager import SourceManager
from system.models import System
from user.models import EntrakUser
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def activate_account(request, user_id):

    user = EntrakUser.objects.get(id=user_id, is_email_verified=False)

    if request.method == 'POST':
        user_id = request.POST.get('uid', None)
        user_code = request.POST.get('ucode', None)
    else:
        user_id = request.GET.get('uid', None)
        user_code = request.GET.get('ucode', None)

    print(user.__dict__)
    print(user_id)
    print(user_code)

    if user and user_id and user_code:

        if user.validate_activation_url(user_id.encode('ascii','ignore'), user_code.encode('ascii','ignore')):
            system = System.objects.get(id=user.system_id)

            if request.method == 'POST':
                user.first_name = request.POST.get('first_name', None)
                user.last_name = request.POST.get('last_name', None)
                user.department = request.POST.get('department', None)
                user.language = request.POST.get('language', None)
                user.password = request.POST.get('password', None)

                print(u.__dict__)

            else:
                m = {"uid": user_id, "ucode": user_code}
                m.update(csrf(request))
                m["system"] = system
                m["user"] = user

                return render(request, 'activate_account.html', m)

        else:
            request.session['login_warning_msg'] = _("Invalid user or token")
            return redirect('/login')

    else:
        request.session['login_warning_msg'] = _("Invalid user or token")
        return redirect('/login')
