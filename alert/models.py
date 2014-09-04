import pytz
import datetime
from django.db import models
from jsonfield import JSONField
from egauge.manager import SourceManager

ALERT_TYPE_CONTINUOUS	= 'continuous'
ALERT_TYPE_PERIOD_END	= 'period_end'
ALERT_TYPE_CHOICES = (
	(ALERT_TYPE_CONTINUOUS, 'continuous'),
	(ALERT_TYPE_PERIOD_END, 'period end'),
)

ALERT_COMPARE_TARGET_RECENT = 'recent'
ALERT_COMPARE_TARGET_THRESHOLD = 'threshold'
ALERT_COMPARE_TARGET_CHOICES = (
	(ALERT_COMPARE_TARGET_RECENT, 'recent'),
	(ALERT_COMPARE_TARGET_THRESHOLD, 'threshold'),
)

ALERT_COMPARE_METHOD_ABOVE = 'above'
ALERT_COMPARE_METHOD_BELOW = 'below'
ALERT_COMPARE_METHOD_CHOICES = (
	(ALERT_COMPARE_METHOD_ABOVE, 'above'),
	(ALERT_COMPARE_METHOD_BELOW, 'below'),
)

CONTINUOUS_INTERVAL_MIN = 5

class Alert(models.Model):
	system = models.ForeignKey('system.System')
	name = models.CharField(max_length=200)
	type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES)
	compare_target = models.CharField(max_length=30, choices=ALERT_COMPARE_TARGET_CHOICES)
	compare_method = models.CharField(max_length=30, choices=ALERT_COMPARE_METHOD_CHOICES)
	compare_percent = models.PositiveSmallIntegerField(blank=True, null=True)
	compare_threshold = models.PositiveIntegerField(blank=True, null=True)
	period_end_last_check = models.DateTimeField(blank=True, null=True)
	start_time = models.TimeField()
	end_time = models.TimeField()
	check_weekdays = JSONField()
	source_info = JSONField()

	def __unicode__(self):
		return '%s'%self.name

	def get_all_source_ids(self):
		source_ids = []
		for info in self.source_info:
			if 'source_ids' in info:
				source_ids += info['source_ids']
			elif 'source_id' in info:
				source_ids.append(info['source_id'])

		return source_ids

	def gen_start_end_dt(self, now):
		if self.type == ALERT_TYPE_CONTINUOUS:
			end_min = (now.minute/CONTINUOUS_INTERVAL_MIN)*CONTINUOUS_INTERVAL_MIN
			end_dt = now.replace(minute=end_min)
			start_dt = end_dt - datetime.timedelta(minutes=CONTINUOUS_INTERVAL_MIN)
		elif self.type == ALERT_TYPE_PERIOD_END:
			start_dt = now.replace(hour=self.start_time.hour, minute=self.start_time.minute)
			end_dt = now.replace(hour=self.end_time.hour, minute=self.end_time.minute)
			if now.time() < self.end_time:
				start_dt -= datetime.timedelta(days=1)
				end_dt -= datetime.timedelta(days=1)

		return (start_dt, end_dt)

	def get_component_val(self, component, val_info):
		if 'source_ids' in component:
			value = 0
			for source_id in component['source_ids']:
				value += val_info[source_id]
		elif 'source_id' in component:
			value = val_info[component['source_id']]

		return value

	def verify(self, utc_now):
		now = utc_now.astimezone(pytz.timezone(self.system.timezone))
		all_source_ids = self.get_all_source_ids()
		start_dt, end_dt = self.gen_start_end_dt(now)
		result = SourceManager.get_readings_sum_info(all_source_ids, start_dt, end_dt)

		fail_components = []
		if self.compare_target == ALERT_COMPARE_TARGET_THRESHOLD:
			for component in self.source_info:
				value = self.get_component_val(component, result)

				if self.compare_method == ALERT_COMPARE_METHOD_ABOVE and value > self.compare_threshold:
					fail_components.append(component)
				elif self.compare_method == ALERT_COMPARE_METHOD_BELOW and value < self.compare_threshold:
					fail_components.append(component)

		elif self.compare_target == ALERT_COMPARE_TARGET_RECENT:
			recent_start_dt = start_dt - datetime.timedelta(days=7)
			recent_end_dt = end_dt - datetime.timedelta(days=7)
			recent_result = SourceManager.get_readings_sum_info(all_source_ids, recent_start_dt, recent_end_dt)

			for component in self.source_info:
				value = self.get_component_val(component, result)
				recent_value = self.get_component_val(component, recent_result)

				if self.compare_method == ALERT_COMPARE_METHOD_ABOVE and value > recent_value*(1+(self.compare_percent/100.0)):
					fail_components.append(component)
				elif self.compare_method == ALERT_COMPARE_METHOD_BELOW and value < recent_value*(1-(self.compare_percent/100.0)):
					fail_components.append(component)

		verify_result = {
			'start_dt': start_dt,
			'end_dt': end_dt,
			'fail_components': fail_components
		}

		return verify_result

class AlertHistory(models.Model):
	alert = models.ForeignKey(Alert)
	created = models.DateTimeField()
	resolved = models.BooleanField()
	fail_components = JSONField(blank=True)

class AlertContact(models.Model):
	alerts = models.ManyToManyField(Alert, blank=True)
	name = models.CharField(max_length=200)
	email = models.EmailField(max_length=254)
	mobile = models.CharField(max_length=30)

class AlertEmail(models.Model):
	to_address = JSONField();
	title = models.CharField(max_length=400)
	content = models.TextField()
