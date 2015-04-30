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
from django.contrib.auth import authenticate
from django.core.urlresolvers import reverse
from django.utils import simplejson
from django.http import HttpResponse

from egauge.manager import SourceManager
from system.models import System
from user.models import EntrakUser
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def activate_account(request, user_id):

    user = None
    data = {}

    users = EntrakUser.objects.filter(id=user_id, is_email_verified=False)
    if users.exists():
        user = users[0]

    if request.is_ajax() and request.method == 'POST':
        data = simplejson.loads(request.body)
        user_id = data.get('uid', None)
        user_code = data.get('ucode', None)
    else:
        user_id = request.GET.get('uid', None)
        user_code = request.GET.get('ucode', None)


    print(user)
    print(user_id)
    print(user_code)


    if user and user_id and user_code:

        if user.validate_activation_url(user_id.encode('ascii','ignore'), user_code.encode('ascii','ignore')):
            system = System.objects.get(id=user.system_id)

            if request.is_ajax() and request.method == 'POST':
                user.first_name = data.get('first_name', None)
                user.last_name = data.get('last_name', None)
                user.username = user.email
                user.department = data.get('department', None)
                user.language = data.get('language', None)
                user.set_password(data.get('password', None))
                user.is_active = True
                user.is_email_verified =  True
                user.save()

                user = authenticate(username=user.username, password=user.password)
                url = reverse('graph', kwargs={'system_code': system.code})
                json_data = simplejson.dumps({"redirect": url})
                return HttpResponse({json_data}, mimetype='application/json')

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
        request.session['login_warning_msg'] = _("Invalid request")
        return redirect('/login')
