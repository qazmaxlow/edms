# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'AlertHistory.threshold'
        db.delete_column(u'alert_alerthistory', 'threshold')

        # Deleting field 'AlertHistory.current_value'
        db.delete_column(u'alert_alerthistory', 'current_value')

        # Adding field 'AlertHistory.threshold_kwh'
        db.add_column(u'alert_alerthistory', 'threshold_kwh',
                      self.gf('django.db.models.fields.FloatField')(null=True),
                      keep_default=False)

        # Adding field 'AlertHistory.current_kwh'
        db.add_column(u'alert_alerthistory', 'current_kwh',
                      self.gf('django.db.models.fields.FloatField')(null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'AlertHistory.threshold'
        db.add_column(u'alert_alerthistory', 'threshold',
                      self.gf('django.db.models.fields.FloatField')(null=True),
                      keep_default=False)

        # Adding field 'AlertHistory.current_value'
        db.add_column(u'alert_alerthistory', 'current_value',
                      self.gf('django.db.models.fields.FloatField')(null=True),
                      keep_default=False)

        # Deleting field 'AlertHistory.threshold_kwh'
        db.delete_column(u'alert_alerthistory', 'threshold_kwh')

        # Deleting field 'AlertHistory.current_kwh'
        db.delete_column(u'alert_alerthistory', 'current_kwh')


    models = {
        u'alert.alert': {
            'Meta': {'object_name': 'Alert'},
            'check_weekdays': ('jsonfield.fields.JSONField', [], {'default': "'[]'", 'blank': 'True'}),
            'compare_method': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'compare_percent': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'contacts': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['contact.Contact']", 'symmetrical': 'False', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'end_time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'peak_threshold': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'source_info': ('jsonfield.fields.JSONField', [], {}),
            'start_time': ('django.db.models.fields.TimeField', [], {'null': 'True', 'blank': 'True'}),
            'summary_last_check': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'system': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['system.System']"}),
            'type': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        u'alert.alertemail': {
            'Meta': {'object_name': 'AlertEmail'},
            'content': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'error': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'recipient': ('django.db.models.fields.EmailField', [], {'max_length': '254'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '400'})
        },
        u'alert.alerthistory': {
            'Meta': {'object_name': 'AlertHistory'},
            'alert': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['alert.Alert']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'current_kwh': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'diff_percent': ('django.db.models.fields.SmallIntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'resolved': ('django.db.models.fields.BooleanField', [], {}),
            'resolved_datetime': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'threshold_kwh': ('django.db.models.fields.FloatField', [], {'null': 'True'})
        },
        u'contact.contact': {
            'Meta': {'object_name': 'Contact'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '254'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mobile': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'system': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['system.System']"})
        },
        u'system.system': {
            'Meta': {'object_name': 'System'},
            'area_sqfoot': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'default': "'hk'", 'max_length': '200'}),
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'company_type': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'first_record': ('django.db.models.fields.DateTimeField', [], {}),
            'full_name': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'full_name_tc': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'intro': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'blank': 'True'}),
            'intro_tc': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'blank': 'True'}),
            'last_update': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'lat': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'lng': ('django.db.models.fields.FloatField', [], {'default': '0'}),
            'login_required': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'logo': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'name_tc': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'night_time_end': ('django.db.models.fields.TimeField', [], {'default': 'datetime.time(7, 0)'}),
            'night_time_start': ('django.db.models.fields.TimeField', [], {'default': 'datetime.time(22, 0)'}),
            'path': ('django.db.models.fields.CharField', [], {'max_length': '2000', 'blank': 'True'}),
            'population': ('django.db.models.fields.PositiveIntegerField', [], {'default': '1'}),
            'timezone': ('django.db.models.fields.CharField', [], {'default': "u'Asia/Hong_Kong'", 'max_length': '50'}),
            'unit_info': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'version': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['alert']