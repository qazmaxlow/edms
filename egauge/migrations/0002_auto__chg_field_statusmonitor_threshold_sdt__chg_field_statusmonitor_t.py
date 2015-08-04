# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'StatusMonitor.threshold_sdt'
        db.alter_column(u'egauge_statusmonitor', 'threshold_sdt', self.gf('django.db.models.fields.TimeField')(null=True))

        # Changing field 'StatusMonitor.threshold_edt'
        db.alter_column(u'egauge_statusmonitor', 'threshold_edt', self.gf('django.db.models.fields.TimeField')(null=True))

    def backwards(self, orm):

        # Changing field 'StatusMonitor.threshold_sdt'
        db.alter_column(u'egauge_statusmonitor', 'threshold_sdt', self.gf('django.db.models.fields.DateTimeField')(null=True))

        # Changing field 'StatusMonitor.threshold_edt'
        db.alter_column(u'egauge_statusmonitor', 'threshold_edt', self.gf('django.db.models.fields.DateTimeField')(null=True))

    models = {
        u'egauge.statusmonitor': {
            'Meta': {'object_name': 'StatusMonitor'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'threshold': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'threshold_edt': ('django.db.models.fields.TimeField', [], {'null': 'True'}),
            'threshold_sdt': ('django.db.models.fields.TimeField', [], {'null': 'True'})
        }
    }

    complete_apps = ['egauge']