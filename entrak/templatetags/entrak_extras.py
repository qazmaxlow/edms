import json
import calendar
import pytz
from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escapejs
from entrak.settings import MEDIA_URL
from alert.models import ALERT_TYPE_STILL_ON, ALERT_TYPE_SUMMARY
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
			'id': system.id,
			'code': system.code,
			'name': system.name, 'nameTc': system.name_tc,
			'intro': system.intro, 'introTc': system.intro_tc,
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
			'name': source.d_name, 'nameTc': source.d_name_tc,
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
			'shortDesc': unit_category.short_desc.replace("CO2", "CO<sub>2</sub>"),
			'name': unit_category.name.replace("CO2", "CO<sub>2</sub>"),
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
		info = {
			'id': alert.id,
			'type': alert.type,
			'comparePercent': alert.compare_percent,
			'peakThreshold': alert.peak_threshold,
			'checkWeekdays': alert.check_weekdays,
			'contactEmails': [email.encode('utf8') for email in alert.contacts.values_list('email', flat=True)],
			'sourceInfo': alert.source_info,
			'created': alert.created.astimezone(pytz.timezone(alert.system.timezone)).strftime("%Y-%m-%d %H:%M:%S")
		}
		if alert.type == ALERT_TYPE_STILL_ON or alert.type == ALERT_TYPE_SUMMARY:
			info['startTime'] = alert.start_time.strftime('%H:%M')
			info['endTime'] = alert.end_time.strftime('%H:%M')

		alert_infos.append(info)
	return escapejs(json.dumps(alert_infos))

@register.filter
def jsonifyPrimitiveObj(targetObj):
	return escapejs(json.dumps(targetObj))
