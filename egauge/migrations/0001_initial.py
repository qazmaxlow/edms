# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'StatusMonitor'
        db.create_table(u'egauge_statusmonitor', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('source_id', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('threshold', self.gf('django.db.models.fields.FloatField')(null=True)),
            ('threshold_sdt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('threshold_edt', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal(u'egauge', ['StatusMonitor'])


    def backwards(self, orm):
        # Deleting model 'StatusMonitor'
        db.delete_table(u'egauge_statusmonitor')


    models = {
        u'egauge.statusmonitor': {
            'Meta': {'object_name': 'StatusMonitor'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'source_id': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'threshold': ('django.db.models.fields.FloatField', [], {'null': 'True'}),
            'threshold_edt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'threshold_sdt': ('django.db.models.fields.DateTimeField', [], {'null': 'True'})
        }
    }

    complete_apps = ['egauge']