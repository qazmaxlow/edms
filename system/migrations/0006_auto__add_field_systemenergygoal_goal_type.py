# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding field 'SystemEnergyGoal.goal_type'
        db.add_column(u'system_systemenergygoal', 'goal_type',
                      self.gf('django.db.models.fields.IntegerField')(default=1),
                      keep_default=False)


    def backwards(self, orm):
        # Deleting field 'SystemEnergyGoal.goal_type'
        db.delete_column(u'system_systemenergygoal', 'goal_type')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
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
        },
        u'system.systemenergygoal': {
            'Meta': {'object_name': 'SystemEnergyGoal'},
            'comparison_type': ('django.db.models.fields.IntegerField', [], {}),
            'created_by': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['user.EntrakUser']"}),
            'created_time': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'goal_type': ('django.db.models.fields.IntegerField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'system': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['system.System']"}),
            'validated_date': ('django.db.models.fields.DateTimeField', [], {})
        },
        u'system.systemhomeimage': {
            'Meta': {'object_name': 'SystemHomeImage'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100'}),
            'system': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['system.System']"})
        },
        u'user.entrakuser': {
            'Meta': {'object_name': 'EntrakUser'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'department': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'device_id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'device_type': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_email_verified': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_personal_account': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'default': "'en'", 'max_length': '10'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'role_level': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1', 'max_length': '20'}),
            'salt': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'system': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['system.System']", 'null': 'True', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        }
    }

    complete_apps = ['system']