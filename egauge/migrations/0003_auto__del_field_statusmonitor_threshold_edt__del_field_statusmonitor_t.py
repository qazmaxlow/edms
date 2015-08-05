# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'StatusMonitor.threshold_edt'
        db.delete_column(u'egauge_statusmonitor', 'threshold_edt')

        # Deleting field 'StatusMonitor.threshold_sdt'
        db.delete_column(u'egauge_statusmonitor', 'threshold_sdt')

        # Adding field 'StatusMonitor.threshold_starttime'
        db.add_column(u'egauge_statusmonitor', 'threshold_starttime',
                      self.gf('django.db.models.fields.TimeField')(null=True),
                      keep_default=False)

        # Adding field 'StatusMonitor.threshold_endtime'
        db.add_column(u'egauge_statusmonitor', 'threshold_endtime',
                      self.gf('django.db.models.fields.TimeField')(null=True),
                      keep_default=False)


    def backwards(self, orm):
        # Adding field 'StatusMonitor.threshold_edt'
        db.add_column(u'egauge_statusmonitor', 'threshold_edt',
                      self.gf('django.db.models.fields.TimeField')(null=True),
                      keep_default=False)

        # Adding field 'StatusMonitor.threshold_sdt'
        db.add_column(u'egauge_statusmonitor', 'threshold_sdt',
                      self.gf('django.db.models.fields.TimeField')(null=True),
                      keep_default=False)

        # Deleting field 'StatusMonitor.threshold_starttime'
        db.delete_column(u'egauge_statusmonitor', 'threshold_starttime')

        # Deleting field 'StatusMonitor.threshold_endtime'
        db.delete_column(u'egauge_statusmonitor', 'threshold_endtime')


    models = {
        u'egauge.statusmonitor': {
            'Meta': {'object_name': 'StatusMonitor'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'threshold': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'threshold_endtime': ('django.db.models.fields.TimeField', [], {'null': 'True'}),
            'threshold_starttime': ('django.db.models.fields.TimeField', [], {'null': 'True'})
        }
    }

    complete_apps = ['egauge']