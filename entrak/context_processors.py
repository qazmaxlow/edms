from settings import ANALYTICS_TRACKING
from django.core.urlresolvers import resolve

def analytics(request):
    if request.user.is_authenticated():
        ga_user_id = '%d|%s'%(request.user.id, request.user.username)
    else:
        ga_user_id = 'anonymous'
    system_code = resolve(request.path).kwargs.get('system_code', '')

    context_extras = {
        'ANALYTICS_TRACKING': ANALYTICS_TRACKING,
        'SYSTEM_CODE': system_code,
        'GA_USER_ID': ga_user_id
    }
    return context_extras
