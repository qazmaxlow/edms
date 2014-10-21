# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UnitCategory'
        db.create_table(u'unit_unitcategory', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('name_tc', self.gf('django.db.models.fields.CharField')(max_length=300, blank=True)),
            ('short_desc', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('short_desc_tc', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('order', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1)),
            ('img_off', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('img_on', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('bg_img', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('is_suffix', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('global_rate', self.gf('django.db.models.fields.FloatField')(default=1)),
            ('has_detail_rate', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('city', self.gf('django.db.models.fields.CharField')(max_length=200)),
        ))
        db.send_create_signal(u'unit', ['UnitCategory'])

        # Adding model 'UnitRate'
        db.create_table(u'unit_unitrate', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('category_code', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('rate', self.gf('django.db.models.fields.FloatField')(default=1)),
            ('effective_date', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'unit', ['UnitRate'])


    def backwards(self, orm):
        # Deleting model 'UnitCategory'
        db.delete_table(u'unit_unitcategory')

        # Deleting model 'UnitRate'
        db.delete_table(u'unit_unitrate')


    models = {
        u'unit.unitcategory': {
            'Meta': {'object_name': 'UnitCategory'},
            'bg_img': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'global_rate': ('django.db.models.fields.FloatField', [], {'default': '1'}),
            'has_detail_rate': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'img_off': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'img_on': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'is_suffix': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'name_tc': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'order': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1'}),
            'short_desc': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'short_desc_tc': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'})
        },
        u'unit.unitrate': {
            'Meta': {'object_name': 'UnitRate'},
            'category_code': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'effective_date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rate': ('django.db.models.fields.FloatField', [], {'default': '1'})
        }
    }

    complete_apps = ['unit']