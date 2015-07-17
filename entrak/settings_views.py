import datetime
import json
import pytz
import calendar
from django.shortcuts import render
from django.core.context_processors import csrf
from django.views.decorators.csrf import ensure_csrf_cookie
from django.utils.translation import ugettext as _
from django.utils.html import escapejs
from django.db.models import Q
from django.db import transaction, IntegrityError
from system.models import System
from egauge.manager import SourceManager
from egauge.models import Source
from alert.models import Alert, AlertHistory, ALERT_TYPE_STILL_ON, ALERT_TYPE_SUMMARY, ALERT_TYPE_PEAK, ALERT_COMPARE_METHOD_ABOVE
from contact.models import Contact
from user.models import EntrakUser, USER_ROLE_ADMIN_LEVEL, USER_ROLE_VIEWER_LEVEL
from utils.auth import permission_required
from utils.utils import Utils
from audit.decorators.trail import log_audit_trail
from constants import audits as constants_audits


SHOW_HISTORY_DAY_MAX = 7


@log_audit_trail(action_type=constants_audits.ACTION_VIEW_ALERT)
@permission_required(USER_ROLE_ADMIN_LEVEL)
@ensure_csrf_cookie
def alert_settings_view(request, system_code=None):
    systems_info = System.get_systems_info(system_code, request.user.system.code)
    current_system = systems_info["systems"][0]
    sources = SourceManager.get_sources(current_system)
    contact_emails = Contact.objects.filter(system__code=system_code).values_list('email', flat=True)
    alerts = Alert.objects.filter(system_id__in=[system.id for system in systems_info["systems"]]).prefetch_related('contacts')

    system_id = current_system.id
    system_timezone = pytz.timezone(current_system.timezone)

    bound_dt = pytz.utc.localize(datetime.datetime.utcnow()) - datetime.timedelta(days=SHOW_HISTORY_DAY_MAX)
    alert_historys = AlertHistory.objects.select_related('alert').filter(
        Q(created__gte=bound_dt) | Q(resolved_datetime__gte=bound_dt),
        alert__system_id=system_id).order_by('-created')

    alert_history_infos = []
    for alert_history in alert_historys:

        system = System.objects.get(code=alert_history.alert.source.system_code)

        info = {
            'created': calendar.timegm(alert_history.created.utctimetuple()),
            'systemInfo': {'en': system.name, 'zh-tw': system.name_tc},
            'nameInfo': alert_history.alert.source_info['nameInfo'],
            'alert_type': alert_history.alert.type,
            'alert_compare_method': alert_history.alert.compare_method,
            'diff_percent': alert_history.diff_percent,
            'check_weekdays': alert_history.alert.check_weekdays,
            'resolved': alert_history.resolved,
        }

        if alert_history.resolved:
            info['resolved_datetime'] = calendar.timegm(alert_history.resolved_datetime.utctimetuple())

        if alert_history.alert.type == ALERT_TYPE_SUMMARY:
            info['start_time_h'] = alert_history.alert.start_time.hour
            info['start_time_m'] = alert_history.alert.start_time.minute
            info['end_time_h'] = alert_history.alert.end_time.hour
            info['end_time_m'] = alert_history.alert.end_time.minute

        alert_history_infos.append(info)

    m = systems_info
    m['sources'] = sources
    m['contact_emails'] = [email.encode('utf8') for email in contact_emails]
    m['alerts'] = alerts
    m['alert_history_infos'] = escapejs(json.dumps(alert_history_infos))
    m.update(csrf(request))

    return render(request, 'alert_settings.html', m)


@permission_required(USER_ROLE_ADMIN_LEVEL)
def set_alert_view(request, system_code=None):
    system_id = request.POST.get('system_id')
    alert_id = request.POST.get('alert_id')
    alert_type = request.POST.get('alert_type')
    source_info = json.loads(request.POST.get('source_info'))
    compare_percent = request.POST.get('compare_percent')
    contact_emails = json.loads(request.POST.get('contact_emails'))

    if alert_type == ALERT_TYPE_PEAK:
        peak_threshold = request.POST.get('peak_threshold')
    elif alert_type == ALERT_TYPE_SUMMARY or alert_type == ALERT_TYPE_STILL_ON:
        start_time = datetime.datetime.strptime(request.POST.get('start_time'), '%H:%M').time()
        end_time = datetime.datetime.strptime(request.POST.get('end_time'), '%H:%M').time()
        check_weekdays = json.loads(request.POST.get('check_weekdays'))

    exist_contact_emails = Contact.objects.filter(system_id=system_id, email__in=contact_emails).values_list('email', flat=True)
    need_add_contacts = []
    for email in contact_emails:
        if email not in exist_contact_emails:
            need_add_contacts.append(Contact(system_id=system_id, email=email))
    Contact.objects.bulk_create(need_add_contacts)
    contact_ids = Contact.objects.filter(system_id=system_id, email__in=contact_emails)

    if alert_id:
        alert = Alert.objects.get(id=alert_id)
        is_edit = True
    else:
        alert = Alert()
        is_edit = False

    alert.system_id = system_id
    alert.type = alert_type
    alert.source_info = source_info
    alert.compare_method = ALERT_COMPARE_METHOD_ABOVE
    alert.compare_percent = compare_percent
    if alert_type == ALERT_TYPE_STILL_ON or alert_type == ALERT_TYPE_SUMMARY:
        alert.start_time = start_time
        alert.end_time = end_time
        alert.check_weekdays = check_weekdays
    elif alert_type == ALERT_TYPE_PEAK:
        alert.peak_threshold = peak_threshold
        alert.check_weekdays = []
    alert.save()
    alert.contacts.clear()
    alert.contacts.add(*contact_ids)

    return Utils.json_response({'success': True, 'alert': alert.to_info(), 'is_edit': is_edit})


@permission_required(USER_ROLE_ADMIN_LEVEL)
def remove_alert_view(request, system_code=None):
    alert_id = request.POST.get('alert_id')

    with transaction.atomic():
        AlertHistory.objects.filter(alert_id=alert_id).delete()
        Alert.objects.filter(id=alert_id).delete()

    return Utils.json_response({'success': True})


@permission_required(USER_ROLE_ADMIN_LEVEL)
@ensure_csrf_cookie
def general_settings_view(request, system_code=None):
    systems_info = System.get_systems_info(system_code, request.user.system.code)
    users = EntrakUser.objects.filter(
        system_id__in=[system.id for system in systems_info["systems"]]
    ).select_related('system_name').order_by('id')

    m = systems_info

    m['general_user_info'] = []
    m['admin_user_info'] = []
    for user in users:
        info = {
            'id': user.id,
            'userName': user.username,
            'systemName': user.system.name,
            'roleLevel': user.role_level,
            'email': user.email,
            'label': user.label
        }
        if user.role_level == USER_ROLE_ADMIN_LEVEL:
            m['admin_user_info'].append(info)
        else:
            m['general_user_info'].append(info)
    m.update(csrf(request))

    return render(request, 'general_settings.html', m)


@permission_required()
def set_user_info_view(request, system_code=None):
    user_id = request.POST.get('id')
    label = request.POST.get('label')
    username = request.POST.get('username')
    email = request.POST.get('email')
    old_pwd = request.POST.get('old_pwd')
    new_pwd = request.POST.get('new_pwd')

    if label == '' or username == '' or email == '':
        is_success = False
    else:
        is_success = True

    result = {}
    if is_success:
        if user_id:
            user = EntrakUser.objects.get(id=user_id)
            user.label = label
            user.email = email

            if user.role_level != USER_ROLE_ADMIN_LEVEL:
                user.username = username

            if old_pwd != '' and new_pwd != '':
                if user.check_password(old_pwd):
                    user.set_password(new_pwd)
                else:
                    result['warning'] = _("Change password failed, old password does not match")

            user.save()

        else:
            try:
                user = EntrakUser.objects.create_user(username, email, new_pwd)
                user.label = label
                user.role_level = USER_ROLE_VIEWER_LEVEL
                user.system = System.objects.get(code=system_code)
                user.save()
                result['created'] = True
            except IntegrityError, e:
                is_success = False
                result['warning'] = _("Username has already been taken")

    if is_success:
        result['user'] = {
            'id': user.id,
            'userName': user.username,
            'systemName': user.system.name,
            'roleLevel': user.role_level,
            'email': user.email,
            'label': user.label
        }

    result['success'] = is_success

    return Utils.json_response(result)


@permission_required(USER_ROLE_ADMIN_LEVEL)
def delete_user_view(request, system_code=None):
    user = EntrakUser.objects.get(id=request.POST.get('id'))
    system = System.objects.get(code=system_code)
    if (user.system.code == system.code or (',%s,'%user.system.code in system.path)) \
        and user.role_level != USER_ROLE_ADMIN_LEVEL and (not user.is_staff) and (not user.is_superuser):
        user.delete()

    return Utils.json_response({'success': True})


@permission_required()
@ensure_csrf_cookie
def profile_view(request, system_code=None):
    systems_info = System.get_systems_info(system_code, request.user.system.code)
    users = EntrakUser.objects.filter(
        system_id__in=[system.id for system in systems_info["systems"]]
    ).select_related('system_name').order_by('id')

    m = systems_info
    m['user'] = request.user

    m.update(csrf(request))

    return render(request, 'profile.html', m)


@permission_required(USER_ROLE_ADMIN_LEVEL)
@ensure_csrf_cookie
def manage_accounts_view(request, system_code=None):

    systems_info = System.get_systems_info(system_code, request.user.system.code)
    system = System.objects.get(code=system_code)

    m = systems_info
    m["system"] = system
    m.update(csrf(request))

    return render(request, 'manage_accounts.html', m)
