from settings import ANALYTICS_TRACKING

def analytics(request):
    context_extras = {'ANALYTICS_TRACKING': ANALYTICS_TRACKING}
    return context_extras
