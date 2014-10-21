# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'UnitType'
        db.create_table(u'unit_unittype', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.SlugField')(max_length=30)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=30)),
        ))
        db.send_create_signal(u'unit', ['UnitType'])

        # Adding M2M table for field unit_type on 'UnitCategory'
        m2m_table_name = db.shorten_name(u'unit_unitcategory_unit_type')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('unitcategory', models.ForeignKey(orm[u'unit.unitcategory'], null=False)),
            ('unittype', models.ForeignKey(orm[u'unit.unittype'], null=False))
        ))
        db.create_unique(m2m_table_name, ['unitcategory_id', 'unittype_id'])


    def backwards(self, orm):
        # Deleting model 'UnitType'
        db.delete_table(u'unit_unittype')

        # Removing M2M table for field unit_type on 'UnitCategory'
        db.delete_table(db.shorten_name(u'unit_unitcategory_unit_type'))


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
            'short_desc_tc': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'unit_type': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'unit_types'", 'symmetrical': 'False', 'to': u"orm['unit.UnitType']"})
        },
        u'unit.unitrate': {
            'Meta': {'object_name': 'UnitRate'},
            'category_code': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'effective_date': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rate': ('django.db.models.fields.FloatField', [], {'default': '1'})
        },
        u'unit.unittype': {
            'Meta': {'object_name': 'UnitType'},
            'code': ('django.db.models.fields.SlugField', [], {'max_length': '30'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        }
    }

    complete_apps = ['unit']