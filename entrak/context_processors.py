from settings import ANALYTICS_TRACKING
from django.core.urlresolvers import resolve

def analytics(request):
    if request.user.is_authenticated():
        ga_user_id = '%d|%s'%(request.user.id, request.user.username)
    else:
        ga_user_id = None
    system_code = resolve(request.path).kwargs.get('system_code', '')

    context_extras = {
        'ANALYTICS_TRACKING': ANALYTICS_TRACKING,
        'SYSTEM_CODE': system_code,
        'GA_USER_ID': ga_user_id
    }
    return context_extras


def version_base_template(request):
    from system.models import System

    tpl_name = 'page_base.html'

    system_code = resolve(request.path).kwargs.get('system_code')

    try:
        system = System.objects.get(code=system_code)
        if system.version == '4.0':
            tpl_name = 'page_base_v4.html'
    except System.DoesNotExist:
        pass

    return {'base_template_name': tpl_name}
