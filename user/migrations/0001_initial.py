# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'EntrakUser'
        db.create_table(u'user_entrakuser', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('password', self.gf('django.db.models.fields.CharField')(max_length=128)),
            ('last_login', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('is_superuser', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('username', self.gf('django.db.models.fields.CharField')(unique=True, max_length=30)),
            ('first_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('last_name', self.gf('django.db.models.fields.CharField')(max_length=30, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=75, blank=True)),
            ('is_staff', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_active', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('date_joined', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('system', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['system.System'], null=True, blank=True)),
            ('role_level', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=1, max_length=20)),
            ('label', self.gf('django.db.models.fields.CharField')(max_length=300, blank=True)),
        ))
        db.send_create_signal(u'user', ['EntrakUser'])

        # Adding M2M table for field groups on 'EntrakUser'
        m2m_table_name = db.shorten_name(u'user_entrakuser_groups')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('entrakuser', models.ForeignKey(orm[u'user.entrakuser'], null=False)),
            ('group', models.ForeignKey(orm[u'auth.group'], null=False))
        ))
        db.create_unique(m2m_table_name, ['entrakuser_id', 'group_id'])

        # Adding M2M table for field user_permissions on 'EntrakUser'
        m2m_table_name = db.shorten_name(u'user_entrakuser_user_permissions')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('entrakuser', models.ForeignKey(orm[u'user.entrakuser'], null=False)),
            ('permission', models.ForeignKey(orm[u'auth.permission'], null=False))
        ))
        db.create_unique(m2m_table_name, ['entrakuser_id', 'permission_id'])


    def backwards(self, orm):
        # Deleting model 'EntrakUser'
        db.delete_table(u'user_entrakuser')

        # Removing M2M table for field groups on 'EntrakUser'
        db.delete_table(db.shorten_name(u'user_entrakuser_groups'))

        # Removing M2M table for field user_permissions on 'EntrakUser'
        db.delete_table(db.shorten_name(u'user_entrakuser_user_permissions'))


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
        u'user.entrakuser': {
            'Meta': {'object_name': 'EntrakUser'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'label': ('django.db.models.fields.CharField', [], {'max_length': '300', 'blank': 'True'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'role_level': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '1', 'max_length': '20'}),
            'system': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['system.System']", 'null': 'True', 'blank': 'True'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        }
    }

    complete_apps = ['user']