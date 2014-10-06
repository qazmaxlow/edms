import json
import calendar
from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escapejs
from entrak.settings import MEDIA_URL, LANG_CODE_EN, LANG_CODE_TC
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
def get_value_with_key(info, key):
	return info[key]

@register.filter
def get_system_name(system, lang_code):
	if lang_code == LANG_CODE_TC:
		system_name = system.name_tc
	else:
		system_name = system.name
	return system_name

@register.filter
def get_system_full_name(system, lang_code):
	if lang_code == LANG_CODE_TC:
		system_full_name = system.full_name_tc
	else:
		system_full_name = system.full_name
	return system_full_name

@register.filter
def jsonifySystems(systems):
	systems_info = []
	for system in systems:
		info = {
			'id': system.id,
			'code': system.code,
			'nameInfo': {LANG_CODE_EN: system.name, LANG_CODE_TC: system.name_tc},
			'path': system.path, 'firstRecord': calendar.timegm(system.first_record.utctimetuple())}
		if system.logo:
			info['logo'] = system.logo.url
		systems_info.append(info)

	return escapejs(json.dumps(systems_info))

@register.filter
def jsonifySources(sources):
	sources_info = []
	for source in sources:
		info = {
			'id': str(source.id),
			'systemCode': source.system_code,
			'nameInfo': {LANG_CODE_EN: source.d_name, LANG_CODE_TC: source.d_name_tc},
			'order': source.order
		}
		sources_info.append(info)

	return escapejs(json.dumps(sources_info))

@register.filter
def jsonifyUnitCategorys(unit_categorys):
	unit_categorys_info = []
	for unit_category in unit_categorys:
		info = {
			'code': unit_category.code,
			'shortDescInfo': {
				LANG_CODE_EN: unit_category.short_desc.replace("CO2", "CO<sub>2</sub>"),
				LANG_CODE_TC: unit_category.short_desc_tc.replace("CO2", "CO<sub>2</sub>")
			},
			'nameInfo': {
				LANG_CODE_EN: unit_category.name.replace("CO2", "CO<sub>2</sub>"),
				LANG_CODE_TC: unit_category.name_tc.replace("CO2", "CO<sub>2</sub>"),
			},
			'imgOff': unit_category.img_off, 'imgOn': unit_category.img_on,
			'bgImg': unit_category.bg_img,
			'hasDetailRate': unit_category.has_detail_rate,
			'globalRate': unit_category.global_rate,
			'isSuffix': unit_category.is_suffix}
		unit_categorys_info.append(info)

	return escapejs(json.dumps(unit_categorys_info))

@register.filter
def jsonifyAlerts(alerts):
	alert_infos = []
	for alert in alerts:
		alert_infos.append(alert.to_info())
	return escapejs(json.dumps(alert_infos))

@register.filter
def jsonifyPrimitiveObj(targetObj):
	return escapejs(json.dumps(targetObj))
