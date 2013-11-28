# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Container'
        db.create_table(u'django_s3_container', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal(u'django_s3', ['Container'])

        # Adding model 'Blob'
        db.create_table(u'django_s3_blob', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('container', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['django_s3.Container'])),
            ('name', self.gf('django.db.models.fields.CharField')(default='J-t-Np611LMSlj36NUq7fb2tC0_04bvM5CCmVHwa-u0v', max_length=44)),
            ('content_type', self.gf('django.db.models.fields.CharField')(default='application/octet-stream', max_length=80)),
            ('size', self.gf('django.db.models.fields.BigIntegerField')(null=True)),
            ('sha256', self.gf('django.db.models.fields.CharField')(max_length=64, blank=True)),
            ('upload_id', self.gf('django.db.models.fields.CharField')(max_length=100, blank=True)),
            ('complete', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal(u'django_s3', ['Blob'])

        # Adding unique constraint on 'Blob', fields ['container', 'name']
        db.create_unique(u'django_s3_blob', ['container_id', 'name'])


    def backwards(self, orm):
        # Removing unique constraint on 'Blob', fields ['container', 'name']
        db.delete_unique(u'django_s3_blob', ['container_id', 'name'])

        # Deleting model 'Container'
        db.delete_table(u'django_s3_container')

        # Deleting model 'Blob'
        db.delete_table(u'django_s3_blob')


    models = {
        u'django_s3.blob': {
            'Meta': {'unique_together': "(('container', 'name'),)", 'object_name': 'Blob'},
            'complete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'container': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['django_s3.Container']"}),
            'content_type': ('django.db.models.fields.CharField', [], {'default': "'application/octet-stream'", 'max_length': '80'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'default': "'f9PjpwrQg3fmlePRgpmvai2VfJ8C632GKPw9LWEy168I'", 'max_length': '44'}),
            'sha256': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'size': ('django.db.models.fields.BigIntegerField', [], {'null': 'True'}),
            'upload_id': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'})
        },
        u'django_s3.container': {
            'Meta': {'object_name': 'Container'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'})
        }
    }

    complete_apps = ['django_s3']