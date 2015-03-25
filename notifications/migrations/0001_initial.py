# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Message'
        db.create_table(u'notifications_message', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('body', self.gf('django.db.models.fields.TextField')()),
            ('is_active', self.gf('django.db.models.fields.BooleanField')()),
            ('pub_date_start', self.gf('django.db.models.fields.DateTimeField')()),
            ('pub_date_end', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal(u'notifications', ['Message'])


    def backwards(self, orm):
        # Deleting model 'Message'
        db.delete_table(u'notifications_message')


    models = {
        u'notifications.message': {
            'Meta': {'object_name': 'Message'},
            'body': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {}),
            'pub_date_end': ('django.db.models.fields.DateTimeField', [], {}),
            'pub_date_start': ('django.db.models.fields.DateTimeField', [], {})
        }
    }

    complete_apps = ['notifications']