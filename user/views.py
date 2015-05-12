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
from django.http import HttpResponseForbidden
from django.http import HttpResponseBadRequest
from django.db import IntegrityError

from egauge.manager import SourceManager
from system.models import System
from user.models import EntrakUser
from utils.utils import Utils
from rest_framework import generics


def activate_account(request, user_id):

    user = None
    data = {}

    users = EntrakUser.objects.filter(id=user_id, is_email_verified=False, is_personal_account=True)
    if users.exists():
        user = users[0]

    if request.is_ajax() and request.method == 'POST':
        data = simplejson.loads(request.body)
        user_id = data.get('uid', None)
        user_code = data.get('ucode', None)
    else:
        user_id = request.GET.get('uid', None)
        user_code = request.GET.get('ucode', None)


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
                dashboard_url = reverse('companies.dashboard', kwargs={'system_code': system.code})
                settings_url = reverse('general_settings', kwargs={'system_code': system.code})
                return Utils.json_response({"dashboard_url": dashboard_url, "settings_url": settings_url})

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


def update_account(request, user_id):

    user = None
    data = simplejson.loads(request.body)

    users = EntrakUser.objects.filter(id=user_id, is_personal_account=True)
    if users.exists():
        user = users[0]

    if user and data:

        first_name = data.get('first_name', None)
        last_name = data.get('last_name', None)
        department = data.get('department', None)
        language = data.get('language', None)
        is_change_pwd = data.get('isChangePwd', False)

        current_password = data.get('current_passowrd', None)
        password = data.get('passowrd', None)
        confirm_password = data.get('confirm_passowrd', None)

        if first_name and last_name and department and language and not is_change_pwd:

            user.first_name = first_name
            user.last_name = last_name
            user.department = department
            user.language = language
            user.save()

            return HttpResponse("User profile updated successfully")

        elif current_passowrd and password and confirm_passowrd and is_change_pwd:

            if password == confirm_password:
                o_user = authenticate(username=user.username, password=current_passowrd)

                if o_user:
                    user.set_password(password)
                    user.save()
                    return HttpResponse("Password updated successfully")
                else:
                    return HttpResponseBadRequest("Current password is incorrect")
            else:
                return HttpResponseBadRequest("Password and confirm password must be the same")

    else:
        return HttpResponseBadRequest("Invalid request")


def send_invitation_email(request, user_id):

    if request.user.is_manager():

        users = EntrakUser.objects.filter(id=user_id, is_email_verified=False, is_personal_account=True)

        if users.exists():
            user = users[0]
            user.send_activation_email(request.user)

            return HttpResponse('<h3>Email Sent</h3>')

        else:
            return HttpResponseBadRequest('<h3>Invalid Request</h3>')


    return HttpResponseForbidden('<h3>Not authorized</h3>')


def create_individual_users(request):
    try:

        data = simplejson.loads(request.body)

        if data.keys() and 'models' in data.keys():
            required_keys = set(['email', 'is_personal_account', 'system_id'])

            for k in data['models']:
                if required_keys.issubset(set(k.keys())):
                    u = EntrakUser.objects.create(username=k['email'], email=k['email'], system_id=k['system_id'], is_personal_account=True)
                    u.send_activation_email()
                else:
                    raise Exception('Invalid request')

            return HttpResponse('Invitation sent successfully')
        else:
            raise Exception('Invalid request')
    except IntegrityError as e:
        return HttpResponseBadRequest("Username is taken already.")


def create_shared_user(request):
    try:

        data = simplejson.loads(request.body)

        if data.keys() and 'models' in data.keys():
            required_keys = set(['username', 'password', 'system_id'])

            for k in data['models']:
                if required_keys.issubset(set(k.keys())):
                    u = EntrakUser.objects.create(username=k['username'], system_id=k['system_id'], is_personal_account=False)
                    u.set_password(k['password'])
                    u.save()
                else:
                    raise Exception('Invalid request')

                return HttpResponse('Shared account created successfully')
        else:
            raise Exception('Invalid request')
    except IntegrityError as e:
        return HttpResponseBadRequest("Username is taken already.")
