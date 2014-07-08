import json
from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escapejs
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

@register.filter
def jsonifySystems(systems):
	systems_info = []
	for system in systems:
		info = {
			'code': system.code,
			'name': system.name, 'nameTc': system.name_tc,
			'intro': system.intro, 'introTc': system.intro_tc,
			'path': system.path}
		systems_info.append(info)

	return escapejs(json.dumps(systems_info))

@register.filter
def jsonifySources(sources):
	sources_info = []
	for source in sources:
		info = {
			'id': str(source.id),
			'systemCode': source.system_code,
			'name': source.d_name, 'nameTc': source.d_name_tc,
			'order': source.order}
		sources_info.append(info)

	return escapejs(json.dumps(sources_info))

@register.filter
def jsonifyUnitCategorys(unit_categorys):
	unit_categorys_info = []
	for unit_category in unit_categorys:
		info = {
			'id': unit_category.id,
			'name': unit_category.name,
			'imgOff': unit_category.img_off, 'imgOn': unit_category.img_on,
			'bgImg': unit_category.bg_img}
		unit_categorys_info.append(info)

	return escapejs(json.dumps(unit_categorys_info))
