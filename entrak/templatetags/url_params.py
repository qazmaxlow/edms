from django.template import Library, TemplateSyntaxError

register = Library()

@register.simple_tag(takes_context=True)
def url_params(context, *args):
    getvars = context['request'].GET.copy()

    try:
        keys = args[0:][::2]
        values = args[1:][::2]
        usrvars = dict(zip(keys, values))
    except (ValueError, IndexError):
        raise TemplateSyntaxError(
            "Unexpected arguments, review your syntax to match {% urlparms 'key' value 'key' value %}")

    for key in usrvars.keys():
        getvars[key] = usrvars[key]

    return getvars.urlencode() 
