# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'Location.timedelta'
        db.alter_column(u'locations', 'timedelta', self.gf('durationfield.db.models.fields.duration.DurationField')(null=True))

    def backwards(self, orm):

        # Changing field 'Location.timedelta'
        db.alter_column(u'locations', 'timedelta', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=9, decimal_places=3))

    models = {
        u'blog.article': {
            'Meta': {'object_name': 'Article', 'db_table': "u'articles'"},
            'datestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'idxfti': ('django.db.models.fields.TextField', [], {}),
            'markdown': ('django.db.models.fields.TextField', [], {}),
            'published': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'searchtext': ('django.db.models.fields.TextField', [], {}),
            'shorttitle': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'blog.comment': {
            'Meta': {'object_name': 'Comment', 'db_table': "u'comments'"},
            'article': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['blog.Article']"}),
            'comment': ('django.db.models.fields.TextField', [], {}),
            'datestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'website': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True'})
        },
        u'blog.location': {
            'Meta': {'object_name': 'Location', 'db_table': "u'locations'"},
            'accuracy': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '6'}),
            'devicetimestamp': ('django.db.models.fields.DateTimeField', [], {}),
            'distance': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '3'}),
            'geocoding': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '9', 'decimal_places': '6'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'max_digits': '9', 'decimal_places': '6'}),
            'timedelta': ('durationfield.db.models.fields.duration.DurationField', [], {'null': 'True'}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['blog']