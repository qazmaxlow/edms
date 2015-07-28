import datetime
import json
import pytz
import re

from dateutil.relativedelta import relativedelta
from django.core.context_processors import csrf
from django.shortcuts import render
from django.shortcuts import redirect
from django.utils import dateparse
from django.utils import timezone
from operator import itemgetter
from django.utils.translation import ugettext as _
from django.contrib.auth import authenticate
from django.contrib.auth import login
from django.core.urlresolvers import reverse
from django.utils import simplejson
from django.http import HttpResponse
from django.http import HttpResponseForbidden
from django.http import HttpResponseBadRequest
from django.db.utils import IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.utils import translation
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import APIException
from rest_framework.exceptions import ParseError

from egauge.manager import SourceManager
from system.models import System
from user.models import EntrakUser
from utils.utils import Utils
from rest_framework import generics
from companies.views.user_views import UserSerializer
from companies.views.user_views import resetPasswordSerializer
from rest_framework import serializers
from django.utils import translation
from entrak.settings_common import LANG_CODE_EN, LANG_CODE_TC

PASSWORD_REGEX = re.compile(r'^.*(?=.{8,})(?=.*[A-Za-z]+)(?=.*\d).*$')


def activate_account(request, user_id):

    # always activate the account in English
    translation.activate(LANG_CODE_EN)

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

        if user.validate_uid_and_ucode(user_id.encode('ascii','ignore'), user_code.encode('ascii','ignore')):
            system = System.objects.get(id=user.system_id)

            if request.is_ajax() and request.method == 'POST':

                if PASSWORD_REGEX.search(data.get('password', None)) is None:
                    return HttpResponse(json.dumps({"error": "Password must be at least 8 characters long and contains at least one character and one number"}), content_type="application/json", status=400)

                user.first_name = data.get('first_name', None)
                user.last_name = data.get('last_name', None)
                user.username = user.email.lower()
                user.department = data.get('department', None)
                user.language = data.get('language', None)
                user.set_password(data.get('password', None))
                user.is_active = True
                user.is_email_verified =  True
                user.save()

                user = authenticate(username=user.username, password=data.get('password', None))
                if user is not None:
                    login(request, user)
                    translation.activate(user.language)

                dashboard_url = reverse('graph', kwargs={'system_code': system.code})
                settings_url = reverse('manage_accounts', kwargs={'system_code': system.code})

                if user.is_manager:
                    return Utils.json_response({"is_manager": True, "dashboard_url": dashboard_url, "settings_url": settings_url})
                else:
                    return Utils.json_response({"is_manager": False, "dashboard_url": dashboard_url})

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

        current_password = data.get('current_password', None)
        password = data.get('password', None)
        confirm_password = data.get('confirm_password', None)

        if first_name and last_name and department and language and not is_change_pwd:

            user.first_name = first_name
            user.last_name = last_name
            user.department = department
            user.language = language
            user.save()

            return HttpResponse("User profile updated successfully")

        elif current_password and password and confirm_password and is_change_pwd:

            if password == confirm_password:
                o_user = authenticate(username=user.username, password=current_password)

                if o_user:
                    user.set_password(password)
                    user.save()
                    return HttpResponse("Password updated successfully")
                else:
                    return HttpResponseBadRequest("Current password is incorrect")
            else:
                return HttpResponseBadRequest("Passwords do not match")

        else:
            return HttpResponseBadRequest("Invalid request")

    else:
        return HttpResponseBadRequest("Invalid request")


def send_invitation_email(request, user_id):

    if request.user.is_manager:

        users = EntrakUser.objects.filter(id=user_id, is_email_verified=False, is_personal_account=True)

        if users.exists():
            user = users[0]
            user.send_activation_email(request.user)

            return HttpResponse('<h3>Email Sent</h3>')

        else:
            return HttpResponseBadRequest('<h3>Invalid Request</h3>')


    return HttpResponseForbidden('<h3>Not authorized</h3>')


def reset_password(request, user_id):

    user = None
    data = {}

    users = EntrakUser.objects.filter(id=user_id, is_personal_account=True)
    if users.exists():
        user = users[0]
        translation.activate(user.language)

    user_id = request.GET.get('uid', None)
    user_code = request.GET.get('ucode', None)

    if user and user_id and user_code:

        if user.validate_uid_and_ucode(user_id.encode('ascii','ignore'), user_code.encode('ascii','ignore')):
            system = System.objects.get(id=user.system_id)

            m = {"uid": user_id, "ucode": user_code}
            m.update(csrf(request))
            m["system"] = system
            m["user"] = user
            m["dashboard_url"] = reverse('graph', kwargs={'system_code': system.code})

            return render(request, 'reset_password.html', m)

        else:
            request.session['login_warning_msg'] = _("Invalid user or token")
            return redirect('/login')

    else:
        request.session['login_warning_msg'] = _("Invalid request")
        return redirect('/login')

class CreateIndividualUserView(generics.CreateAPIView):

    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):

        data = request.data
        required_keys = set(['email', 'is_personal_account', 'system_id'])

        if not required_keys.issubset(set(data.keys())):
            raise ParseError('Invalid request')

        try:
            u = EntrakUser.objects.create(
                    username=data['email'],
                    email=data['email'],
                    system_id=data['system_id'],
                    is_personal_account=True
                )
            u.send_activation_email(request.user)
        except IntegrityError as e:
            raise serializers.ValidationError("Username %s is taken already." % data['email'])

        user = UserSerializer(u)
        return Response(user.data)


class CreateSharedUserView(generics.CreateAPIView):

    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)

    def post(self, request, format=None):

        data = request.data
        required_keys = set(['username', 'password', 'confirm_password', 'system_id'])

        if not required_keys.issubset(set(data.keys())):
            raise ParseError('Invalid request')

        # validations
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Password does not match")

        if PASSWORD_REGEX.search(data['password']) is None:
            raise serializers.ValidationError("Password must be at least 8 characters long and contains at least one character and one number")

        try:
            u = EntrakUser.objects.create(username=data['username'], system_id=data['system_id'], is_personal_account=False)
            u.set_password(data['password'])
            u.save()
        except IntegrityError as e:
            raise serializers.ValidationError("Username %s is taken already." % data['username'])

        user = UserSerializer(u)
        return Response(user.data)


class DeleteUserView(generics.DestroyAPIView):

    serializer_class = UserSerializer
    permission_classes = (IsAuthenticated,)
    queryset = EntrakUser.objects.all()
    lookup_field = 'user_id'
    lookup_url_kwarg = 'user_id'

    def delete(self, request, *args, **kwargs):

        data = self.request.data
        request_user = self.request.user
        user_to_be_deleted = EntrakUser.objects.get(id=self.kwargs['user_id'])

        system_info = System.get_systems_info(user_to_be_deleted.system.code, request_user.system.code)

        if not system_info or not request_user.is_manager:
            raise PermissionDenied()

        user_to_be_deleted.is_active = False
        user_to_be_deleted.save()

        user = UserSerializer(user_to_be_deleted)
        return Response(user.data)


class UpdateUserView(generics.UpdateAPIView):
    serializer_class = resetPasswordSerializer
    permission_classes = (IsAuthenticated,)
    lookup_field = 'user_id'
    lookup_url_kwarg = 'user_id'

    def put(self, request, *args, **kwargs):

        request_user = self.request.user
        user = EntrakUser.objects.get(id=self.kwargs['user_id'])
        system_info = System.get_systems_info(user.system.code, request_user.system.code)

        request_data = {
            'username': user.username,
            'new_password': request.data.get('new_password', None),
            'confirm_password': request.data.get('confirm_password', None)
        }

        if user.id == request_user.id:
            request_data['current_password'] = request.data.get('current_password', None)
        elif not system_info or not request_user.is_manager:
            raise PermissionDenied()

        serializer = resetPasswordSerializer(user, data=request_data)

        serializer.is_valid(raise_exception=True)
        user.set_password(request.data.get('new_password', None))
        user.save()
        return Response(serializer.data)


class SendPasswordResetEmailView(generics.CreateAPIView):

    serializer_class = UserSerializer

    def post(self, request, format=None):

        data = request.data
        required_keys = set(['email'])

        if not required_keys.issubset(set(data.keys())):
            raise ParseError('Invalid request')

        try:
            u = EntrakUser.objects.get(email=data['email'], is_personal_account=True)
            u.send_password_reset_email()
        except ObjectDoesNotExist as e:
            raise serializers.ValidationError(_("This email is not linked to any existing account."))

        user = UserSerializer(u)
        return Response(user.data)


class ResetPasswordView(generics.UpdateAPIView):

    serializer_class = resetPasswordSerializer
    lookup_field = 'user_id'
    lookup_url_kwarg = 'user_id'

    def put(self, request, *args, **kwargs):

        user = EntrakUser.objects.get(id=self.kwargs['user_id'])

        request_data = {
            'username': user.username,
            'new_password': request.data.get('new_password', None),
            'confirm_password': request.data.get('confirm_password', None)
        }

        serializer = resetPasswordSerializer(user, data=request_data)
        serializer.is_valid(raise_exception=True)

        user.set_password(request.data.get('new_password', None))
        user.save()

        user = authenticate(username=user.username, password=request.data.get('new_password', None))

        if user is not None:
            login(request, user)

        return Response(serializer.data)
