import pytz
import datetime
from django.db import models
from django.core.urlresolvers import reverse
from jsonfield import JSONField
from egauge.manager import SourceManager
from entrak.settings import SITE_LINK_FORMAT

ALERT_TYPE_STILL_ON		= 'still_on'
ALERT_TYPE_SUMMARY		= 'summary'
ALERT_TYPE_PEAK			= 'peak'
ALERT_TYPE_CHOICES = (
	(ALERT_TYPE_STILL_ON, 'still on'),
	(ALERT_TYPE_SUMMARY, 'summary'),
	(ALERT_TYPE_PEAK, 'peak'),
)

ALERT_COMPARE_METHOD_ABOVE = 'above'
ALERT_COMPARE_METHOD_BELOW = 'below'
ALERT_COMPARE_METHOD_CHOICES = (
	(ALERT_COMPARE_METHOD_ABOVE, 'above'),
	(ALERT_COMPARE_METHOD_BELOW, 'below'),
)

CONTINUOUS_INTERVAL_MIN = 5
PEAK_THRESHOLD_FACTOR = 0.9

ALERT_EMAIL_TITLE = u'En-trak Alert: %s'
ALERT_EMAIL_CONTENT_UNRESOLVED = u'''
En-trak has detected that your energy use is not normal in some areas.

%s

When this problem has been resolved, you will receive another notification email.
'''
ALERT_EMAIL_CONTENT_RESOLVED = u'''
One or more of your previously activated alerts has been resolved.

%s

If this issue occurs again, you will receive a new, separate alert.
'''
ALERT_EMAIL_TITLE_STILL_ON = u'Something is still on!'
ALERT_EMAIL_TITLE_SUMMARY = u'Summary alert'
ALERT_EMAIL_TITLE_PEAK = u'Peak demand'

class Alert(models.Model):
	system = models.ForeignKey('system.System')
	type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES)
	compare_method = models.CharField(max_length=30, choices=ALERT_COMPARE_METHOD_CHOICES, blank=True)
	compare_percent = models.PositiveSmallIntegerField(blank=True, null=True)
	peak_threshold = models.PositiveIntegerField(blank=True, null=True)
	summary_last_check = models.DateTimeField(blank=True, null=True)
	start_time = models.TimeField(blank=True, null=True)
	end_time = models.TimeField(blank=True, null=True)
	check_weekdays = JSONField(blank=True, default='[]')
	source_info = JSONField()
	contacts = models.ManyToManyField('contact.Contact', blank=True)
	created = models.DateTimeField(auto_now_add=True)

	def __unicode__(self):
		return '%d'%self.id

	def get_all_source_ids(self):
		if 'source_ids' in self.source_info:
			source_ids = self.source_info['source_ids']
		elif 'source_id' in self.source_info:
			source_ids = [self.source_info['source_id']]

		return source_ids

	def gen_start_end_dt(self, now):
		if self.type == ALERT_TYPE_STILL_ON or self.type == ALERT_TYPE_PEAK:
			end_min = (now.minute/CONTINUOUS_INTERVAL_MIN)*CONTINUOUS_INTERVAL_MIN
			end_dt = now.replace(minute=end_min)
			start_dt = end_dt - datetime.timedelta(minutes=CONTINUOUS_INTERVAL_MIN)
		elif self.type == ALERT_TYPE_SUMMARY:
			start_dt = now.replace(hour=self.start_time.hour, minute=self.start_time.minute)
			end_dt = now.replace(hour=self.end_time.hour, minute=self.end_time.minute)
			if now.time() < self.end_time:
				start_dt -= datetime.timedelta(days=1)
				end_dt -= datetime.timedelta(days=1)

		return (start_dt, end_dt)

	def verify(self, utc_now):
		now = utc_now.astimezone(pytz.timezone(self.system.timezone))
		all_source_ids = self.get_all_source_ids()
		start_dt, end_dt = self.gen_start_end_dt(now)
		value = SourceManager.get_readings_sum(all_source_ids, start_dt, end_dt)

		pass_verify = True
		diff_percent = None
		if self.type == ALERT_TYPE_PEAK:
			if value > self.peak_threshold*PEAK_THRESHOLD_FACTOR:
				pass_verify = False
			diff_percent = int((float(value)/self.peak_threshold)*100)

		elif self.type == ALERT_TYPE_STILL_ON or self.type == ALERT_TYPE_SUMMARY:
			recent_start_dt = start_dt - datetime.timedelta(days=7)
			recent_end_dt = end_dt - datetime.timedelta(days=7)
			recent_value = SourceManager.get_readings_sum(all_source_ids, recent_start_dt, recent_end_dt)

			if self.compare_method == ALERT_COMPARE_METHOD_ABOVE:
				if value > recent_value*(1+(self.compare_percent/100.0)):
					pass_verify = False
			elif self.compare_method == ALERT_COMPARE_METHOD_BELOW:
				if value < recent_value*(1-(self.compare_percent/100.0)):
					pass_verify = False
			diff_percent = int(((float(value)/recent_value)-1)*100)

		verify_result = {
			'start_dt': start_dt,
			'end_dt': end_dt,
			'pass_verify': pass_verify,
			'diff_percent': diff_percent
		}

		return verify_result

	def gen_email_title(self):
		if self.type == ALERT_TYPE_STILL_ON:
			substitute_text = ALERT_EMAIL_TITLE_STILL_ON
		elif self.type == ALERT_TYPE_SUMMARY:
			substitute_text = ALERT_EMAIL_TITLE_SUMMARY
		elif self.type == ALERT_TYPE_PEAK:
			substitute_text = ALERT_EMAIL_TITLE_PEAK

		return ALERT_EMAIL_TITLE%(substitute_text)

	def gen_email_sub_msg(self, info):
		if info['pass_verify']:
			sub_msg = 'RESOLVED - '
		else:
			sub_msg = ''
		sub_msg += info['start_dt'].strftime('%d %b %Y, %I:%M%p')
		sub_msg += info['end_dt'].strftime('-%I:%M%p')
		sub_msg += '   %s'%(self.source_info['name'])
		sub_msg += '   %d%%'%abs(info['diff_percent'])
		if self.type == ALERT_TYPE_PEAK:
			sub_msg += '  of previous peak of %d kVA'%self.peak_threshold
		else:
			if info['diff_percent'] >= 0:
				sub_msg += '  higher'
			else:
				sub_msg += '  lower'
			sub_msg += ' than recent average'

		return sub_msg

	@staticmethod
	def gen_email_content(info):
		email_content = ""
		if info['alert_sub_msgs']:
			email_content += ALERT_EMAIL_CONTENT_UNRESOLVED%('\n'.join(info['alert_sub_msgs']))
		if info['resolved_sub_msgs']:
			email_content += ALERT_EMAIL_CONTENT_RESOLVED%('\n'.join(info['resolved_sub_msgs']))

		if "%s" in SITE_LINK_FORMAT:
			link_prefix = SITE_LINK_FORMAT%info['system_city']
		else:
			link_prefix = SITE_LINK_FORMAT
		email_content +=  '\n\n' + link_prefix \
			+ reverse('settings', kwargs={'system_code': info['system_code'], 'settings_type': 'alert'})

		return email_content

class AlertHistory(models.Model):
	alert = models.ForeignKey(Alert)
	created = models.DateTimeField()
	resolved = models.BooleanField()
	diff_percent = models.SmallIntegerField()

class AlertEmail(models.Model):
	created = models.DateTimeField(auto_now_add=True)
	recipient = models.EmailField(max_length=254)
	title = models.CharField(max_length=400)
	content = models.TextField()
	error = models.TextField(blank=True)
