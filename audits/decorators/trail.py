from functools import wraps

from django.utils.decorators import available_attrs

from audits.models import Trail


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def log_audit_trail(action_type):
    """
    Decorator to audit trails
    """
    def decorator(func):
        @wraps(func, assigned=available_attrs(func))
        def inner(request, *args, **kwargs):
            Trail.objects.create(action_type=action_type,
                          user=request.user,
                          session_key=request.session.session_key,
                          ip_address=get_client_ip(request),
                          url=request.build_absolute_uri()
            )

            return func(request, *args, **kwargs)
        return inner
    return decorator
