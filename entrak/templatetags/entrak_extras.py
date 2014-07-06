from django import template
register = template.Library()

@register.filter
def round_if_larger_than_10(val):
	if val >= 10:
		result = "%.0f" % val
	else:
		result = "%.1f" % val
	return result

@register.filter
def abs_int(val):
	return abs(int(val))

@register.filter
def abs_float(val):
	return abs(float(val))
