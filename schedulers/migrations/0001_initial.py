# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'AutoSendReportSchedular'
        db.create_table(u'schedulers_autosendreportschedular', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('system', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['system.System'])),
            ('created_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('last_execute_time', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('frequency', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal(u'schedulers', ['AutoSendReportSchedular'])

        # Adding model 'AutoSendReportReciever'
        db.create_table(u'schedulers_autosendreportreciever', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('scheduler', self.gf('django.db.models.fields.related.ForeignKey')(related_name='recievers', to=orm['schedulers.AutoSendReportSchedular'])),
            ('email', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal(u'schedulers', ['AutoSendReportReciever'])


    def backwards(self, orm):
        # Deleting model 'AutoSendReportSchedular'
        db.delete_table(u'schedulers_autosendreportschedular')

        # Deleting model 'AutoSendReportReciever'
        db.delete_table(u'schedulers_autosendreportreciever')


    models = {
        u'schedulers.autosendreportreciever': {
            'Meta': {'object_name': 'AutoSendReportReciever'},
            'email': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'scheduler': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'recievers'", 'to': u"orm['schedulers.AutoSendReportSchedular']"})
        },
        u'schedulers.autosendreportschedular': {
            'Meta': {'object_name': 'AutoSendReportSchedular'},
            'created_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'frequency': ('django.db.models.fields.PositiveIntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_execute_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'system': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['system.System']"})
        },
        u'system.system': {
            'Meta': {'object_name': 'System'},
            'area_sqfoot': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'default': "'hk'", 'max_length': '200'}),
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
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
            'unit_info': ('django.db.models.fields.TextField', [], {'default': "'{}'"})
        }
    }

    complete_apps = ['schedulers']