from django.db import models
from jsonfield import JSONField

ALERT_TYPE_CONTINUOUS	= 'continuous'
ALERT_TYPE_PERIOD_END	= 'period_end'
ALERT_TYPE_CHOICES = (
	(ALERT_TYPE_CONTINUOUS, 'continuous'),
	(ALERT_TYPE_PERIOD_END, 'period end'),
)

ALERT_COMPARE_TYPE_RECENT = 'recent'
ALERT_COMPARE_TYPE_THRESHOLD = 'threshold'
ALERT_COMPARE_TYPE_CHOICES = (
	(ALERT_COMPARE_TYPE_RECENT, 'recent'),
	(ALERT_COMPARE_TYPE_THRESHOLD, 'threshold'),
)

ALERT_COMPARE_METHOD_ABOVE = 'above'
ALERT_COMPARE_METHOD_BELOW = 'below'
ALERT_COMPARE_METHOD_CHOICES = (
	(ALERT_COMPARE_METHOD_ABOVE, 'above'),
	(ALERT_COMPARE_METHOD_BELOW, 'below'),
)

class Alert(models.Model):
	system = models.ForeignKey('system.System')
	name = models.CharField(max_length=200)
	type = models.CharField(max_length=30, choices=ALERT_TYPE_CHOICES)
	compare_type = models.CharField(max_length=30, choices=ALERT_COMPARE_TYPE_CHOICES)
	compare_method = models.CharField(max_length=30, choices=ALERT_COMPARE_METHOD_CHOICES)
	compare_percent = models.PositiveSmallIntegerField()
	utc_start_time = models.TimeField()
	utc_end_time = models.TimeField()
	check_weekdays = JSONField()
	source_info = JSONField()

class AlertHistory(models.Model):
	alert = models.ForeignKey(Alert)
	created = models.DateTimeField()
	resolved = models.BooleanField()

class AlertContact(models.Model):
	name = models.CharField(max_length=200)
	email = models.EmailField(max_length=254)
	mobile = models.CharField(max_length=30)

class AlertContactProfile(models.Model):
	pass
