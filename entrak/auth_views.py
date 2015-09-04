from django.shortcuts import redirect
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render
from django.core.context_processors import csrf
from django.utils.http import is_safe_url
from django.utils.translation import ugettext as _
from system.models import System


def login_view(request, system_code=None):
    system = System.objects.get(code=system_code)
    warning_msg = request.session.get('login_warning_msg', '')
    if 'login_warning_msg' in request.session:
        del request.session['login_warning_msg']

    if request.method == 'POST':
        username = request.POST.get('username','').lower()
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)

            if request.POST.get('remember_me', None):
                request.session.set_expiry(365 * 24 * 3600)

            return redirect('companies.dashboard', system_code=system_code)

        else:
            warning_msg = _("Username or password incorrect")

    m = {}
    m.update(csrf(request))
    m["system"] = system
    m["warning_msg"] = warning_msg

    return render(request, 'login.html', m)


def logout_view(request, system_code=None):
    logout(request)
    return redirect('login', system_code=system_code)


def centeral_login_view(request):

    warning_msg = request.session.get('login_warning_msg', '')
    next_url = request.GET.get('next', None)

    if 'login_warning_msg' in request.session:
        del request.session['login_warning_msg']

    if request.method == 'POST':
        username = request.POST.get('username','').lower()
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)

        if user is not None:
            login(request, user)

            redirect_url = request.POST.get('next_url', None)

            if is_safe_url(url=redirect_url, host=request.get_host()):
                return redirect(redirect_url)
            else:
                return redirect('companies.dashboard', system_code=user.system.code)
        else:
            warning_msg = _("Username or password incorrect")

    m = {}
    m.update(csrf(request))
    m["warning_msg"] = warning_msg
    m["next_url"] = next_url
    return render(request, 'central_login.html', m)
