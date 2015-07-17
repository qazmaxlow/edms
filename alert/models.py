import pytz
import datetime
from django.db import models
from django.core.urlresolvers import reverse
from jsonfield import JSONField
from egauge.manager import SourceManager
from egauge.models import Source
from system.models import System
from entrak.settings import SITE_LINK_FORMAT, LANG_CODE_EN

ALERT_TYPE_STILL_ON     = 'still_on'
ALERT_TYPE_SUMMARY      = 'summary'
ALERT_TYPE_PEAK         = 'peak'
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
    ('above-threshold', 'above threshold'),
)

CONTINUOUS_INTERVAL_MIN = 10
KVA_TO_KWH_FACTOR = 0.95
MAX_DIFF_PERCENT_DISPLAY = 1000

ALERT_EMAIL_TITLE = u'En-trak Alert: %s'
ALERT_EMAIL_CONTENT_UNRESOLVED = u'''
En-trak has detected that your energy use is not normal in some areas.

%s

When this problem has been resolved, you will receive another notification email.
'''
ALERT_EMAIL_CONTENT_RESOLVED = u'''
One or more of your previously activated alerts has been resolved at %s.

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

    @property
    def source(self):
        return Source.objects.get(id=self.all_source_ids[0])

    @property
    def parent_system(self):
        return System.objects.get(code=self.source.system_code)

    @property
    def parent_system_name(self):
        system = self.parent_system
        return {'en': system.full_name, 'zh-tw': system.full_name_tc}

    @property
    def source_name(self):
        source = self.source
        return {'en': source.d_name, 'zh-tw': source.d_name_tc}

    def __unicode__(self):
        return '%d'%self.id

    @property
    def all_source_ids(self):
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
        all_source_ids = self.all_source_ids
        start_dt, end_dt = self.gen_start_end_dt(now)
        value, num_of_reading = SourceManager.get_readings_sum(all_source_ids, start_dt, end_dt)

        pass_verify = True
        diff_percent = None
        threshold = None
        current_value = None

        # need to make sure summary and still on alert don't have missing data
        if self.type == ALERT_TYPE_SUMMARY \
            or (num_of_reading == len(all_source_ids)*CONTINUOUS_INTERVAL_MIN):

            if self.type == ALERT_TYPE_PEAK:

                transformed_peak_threshold = self.peak_threshold*KVA_TO_KWH_FACTOR*(CONTINUOUS_INTERVAL_MIN/60.0)
                threshold_kwh = transformed_peak_threshold
                current_kwh = value

                if value > transformed_peak_threshold*(self.compare_percent/100.0):
                    pass_verify = False
                diff_percent = int((float(value)/transformed_peak_threshold)*100)

            elif self.type == ALERT_TYPE_STILL_ON or self.type == ALERT_TYPE_SUMMARY:
                recent_start_dt = start_dt
                recent_end_dt = end_dt

                recent_value = 0
                num_of_compare_weeks = 4
                for x in range(num_of_compare_weeks):
                    recent_start_dt = recent_start_dt - datetime.timedelta(days=7)
                    recent_end_dt = recent_end_dt - datetime.timedelta(days=7)
                    _recent_value, recent_num_of_reading = SourceManager.get_readings_sum(all_source_ids, recent_start_dt, recent_end_dt)
                    recent_value += _recent_value

                recent_value = float(recent_value)/num_of_compare_weeks

                if recent_value != 0:

                    threshold_kwh = recent_value
                    current_kwh = value

                    if self.compare_method == ALERT_COMPARE_METHOD_ABOVE:
                        if value > recent_value*(1+(self.compare_percent/100.0)):
                            pass_verify = False
                    elif self.compare_method == ALERT_COMPARE_METHOD_BELOW:
                        if value < recent_value*(1-(self.compare_percent/100.0)):
                            pass_verify = False
                    elif self.compare_method == 'above-threshold':
                        if value > self.peak_threshold:
                            pass_verify = False

                    if self.compare_method == 'above-threshold':
                        diff_percent = int(float(value - self.peak_threshold)/self.peak_threshold*100)
                    else:
                        diff_percent = int(((float(value)/recent_value)-1)*100)

        verify_result = {
            'start_dt': start_dt,
            'end_dt': end_dt,
            'pass_verify': False,
            'threshold_kwh' : threshold_kwh,
            'current_kwh' : current_kwh,
            'diff_percent': diff_percent,
        }

        return verify_result

    def gen_email_title(self, resolved):
        if resolved:
            substitute_text = "RESOLVED"
        else:
            substitute_text = "ACTIVATED"

        return ALERT_EMAIL_TITLE%(substitute_text)

    def gen_email_sub_msg(self, info, prev_history):

        full_name = self.parent_system_name

        if info['pass_verify']:
            sub_msg = "RESOLVED - "
            created_dt = prev_history.created.astimezone(pytz.timezone(self.system.timezone))
            history_start_dt, history_end_dt = self.gen_start_end_dt(created_dt)
            sub_msg += created_dt.strftime('%d %b %Y')
            sub_msg += history_start_dt.strftime(', %I:%M%p')
            sub_msg += history_end_dt.strftime('-%I:%M%p')
        else:
            sub_msg = ""
            sub_msg += info['start_dt'].strftime('%d %b %Y, %I:%M%p')
            sub_msg += info['end_dt'].strftime('-%I:%M%p')

        sub_msg += '   %s - %s'%(full_name[LANG_CODE_EN], self.source_info['nameInfo'][LANG_CODE_EN])

        if (not info['pass_verify']) and info['diff_percent'] is not None:
            diff_percent_text = "%d"%abs(info['diff_percent']) if abs(info['diff_percent']) <= MAX_DIFF_PERCENT_DISPLAY else ">%d"%MAX_DIFF_PERCENT_DISPLAY
            sub_msg += '   %s%%'%diff_percent_text

        if self.type == ALERT_TYPE_PEAK:
            sub_msg += '  of previous peak of %d kVA'%self.peak_threshold
        else:
            if self.compare_method == 'above-threshold':
                sub_msg += ' higher than your set threshold'
            else:
                sub_msg += '  higher than recent average'

        return sub_msg

    def to_info(self):
        info = {
            'id': self.id,
            'type': self.type,
            'comparePercent': self.compare_percent,
            'peakThreshold': self.peak_threshold,
            'checkWeekdays': self.check_weekdays,
            'contactEmails': [email.encode('utf8') for email in self.contacts.values_list('email', flat=True)],
            'sourceInfo': self.source_info,
            'created': self.created.astimezone(pytz.timezone(self.system.timezone)).strftime("%Y-%m-%d %H:%M:%S")
        }
        if self.type == ALERT_TYPE_STILL_ON or self.type == ALERT_TYPE_SUMMARY:
            info['startTime'] = self.start_time.strftime('%H:%M')
            info['endTime'] = self.end_time.strftime('%H:%M')

        return info

    @staticmethod
    def gen_email_content(info, check_dt):
        if info['resolved']:
            email_content = ALERT_EMAIL_CONTENT_RESOLVED%(
                check_dt.astimezone(pytz.timezone(info["system_timezone"])).strftime("%d %b %Y, %I:%M%p"),
                '\n'.join(info['sub_msgs'])
            )
        else:
            email_content = ALERT_EMAIL_CONTENT_UNRESOLVED%('\n'.join(info['sub_msgs']))

        link_prefix = SITE_LINK_FORMAT
        email_content +=  '\n\n' + link_prefix \
            + reverse('alert_settings', kwargs={'system_code': info['system_code']})

        return email_content

class AlertHistory(models.Model):
    alert = models.ForeignKey(Alert)
    created = models.DateTimeField()
    resolved = models.BooleanField()
    resolved_datetime = models.DateTimeField(blank=True, null=True)
    diff_percent = models.SmallIntegerField()
    threshold_kwh = models.FloatField(null=True)
    current_kwh = models.FloatField(null=True)

class AlertEmail(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    recipient = models.EmailField(max_length=254)
    title = models.CharField(max_length=400)
    content = models.TextField()
    error = models.TextField(blank=True)
