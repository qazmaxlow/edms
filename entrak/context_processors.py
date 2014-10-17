from settings import ANALYTICS_TRACKING
from django.core.urlresolvers import resolve

def analytics(request):
    system_code = resolve(request.path).kwargs.get('system_code', '')
    context_extras = {'ANALYTICS_TRACKING': ANALYTICS_TRACKING, 'SYSTEM_CODE': system_code}
    return context_extras
