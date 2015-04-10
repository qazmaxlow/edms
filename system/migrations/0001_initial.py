# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'System'
        db.create_table(u'system_system', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('name_tc', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('full_name', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('full_name_tc', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('intro', self.gf('django.db.models.fields.CharField')(max_length=2000, blank=True)),
            ('intro_tc', self.gf('django.db.models.fields.CharField')(max_length=2000, blank=True)),
            ('path', self.gf('django.db.models.fields.CharField')(max_length=2000, blank=True)),
            ('logo', self.gf('django.db.models.fields.files.ImageField')(max_length=100, blank=True)),
            ('last_update', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
            ('lat', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('lng', self.gf('django.db.models.fields.FloatField')(default=0)),
            ('city', self.gf('django.db.models.fields.CharField')(default='hk', max_length=200)),
            ('timezone', self.gf('django.db.models.fields.CharField')(default=u'Asia/Hong_Kong', max_length=50)),
            ('population', self.gf('django.db.models.fields.PositiveIntegerField')(default=1)),
            ('first_record', self.gf('django.db.models.fields.DateTimeField')()),
            ('night_time_start', self.gf('django.db.models.fields.TimeField')(default=datetime.time(22, 0))),
            ('night_time_end', self.gf('django.db.models.fields.TimeField')(default=datetime.time(7, 0))),
            ('login_required', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('unit_info', self.gf('django.db.models.fields.TextField')(default='{}')),
        ))
        db.send_create_signal(u'system', ['System'])

        # Adding model 'SystemHomeImage'
        db.create_table(u'system_systemhomeimage', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100)),
            ('system', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['system.System'])),
        ))
        db.send_create_signal(u'system', ['SystemHomeImage'])


    def backwards(self, orm):
        # Deleting model 'System'
        db.delete_table(u'system_system')

        # Deleting model 'SystemHomeImage'
        db.delete_table(u'system_systemhomeimage')


    models = {
        u'system.system': {
            'Meta': {'object_name': 'System'},
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
        },
        u'system.systemhomeimage': {
            'Meta': {'object_name': 'SystemHomeImage'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'system': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['system.System']"})
        }
    }

    complete_apps = ['system']