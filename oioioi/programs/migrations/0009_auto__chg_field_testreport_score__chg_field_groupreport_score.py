# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Changing field 'TestReport.score'
        db.alter_column(u'programs_testreport', 'score', self.gf('oioioi.contests.fields.ScoreField')(max_length=255, null=True))

        # Changing field 'GroupReport.score'
        db.alter_column(u'programs_groupreport', 'score', self.gf('oioioi.contests.fields.ScoreField')(max_length=255, null=True))

    def backwards(self, orm):

        # Changing field 'TestReport.score'
        db.alter_column(u'programs_testreport', 'score', self.gf('oioioi.contests.fields.ScoreField')(default='', max_length=255))

        # User chose to not deal with backwards NULL issues for 'GroupReport.score'
        raise RuntimeError("Cannot reverse this migration. 'GroupReport.score' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration
        # Changing field 'GroupReport.score'
        db.alter_column(u'programs_groupreport', 'score', self.gf('oioioi.contests.fields.ScoreField')(max_length=255))

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
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'contests.contest': {
            'Meta': {'object_name': 'Contest'},
            'controller_name': ('oioioi.base.fields.DottedNameField', [], {'max_length': '255', 'superclass': "'oioioi.contests.controllers.ContestController'"}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'default_submissions_limit': ('django.db.models.fields.IntegerField', [], {'default': '10', 'blank': 'True'}),
            'id': ('django.db.models.fields.CharField', [], {'max_length': '32', 'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        u'contests.probleminstance': {
            'Meta': {'ordering': "('round', 'short_name')", 'unique_together': "(('contest', 'short_name'),)", 'object_name': 'ProblemInstance'},
            'contest': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contests.Contest']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'problem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['problems.Problem']"}),
            'round': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contests.Round']", 'null': 'True', 'blank': 'True'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'submissions_limit': ('django.db.models.fields.IntegerField', [], {'default': '10', 'blank': 'True'})
        },
        u'contests.round': {
            'Meta': {'ordering': "('contest', 'start_date')", 'unique_together': "(('contest', 'name'),)", 'object_name': 'Round'},
            'contest': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contests.Contest']"}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_trial': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'results_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'})
        },
        u'contests.submission': {
            'Meta': {'object_name': 'Submission'},
            'comment': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'date': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('oioioi.base.fields.EnumField', [], {'default': "'NORMAL'", 'max_length': '64'}),
            'problem_instance': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contests.ProblemInstance']"}),
            'score': ('oioioi.contests.fields.ScoreField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'status': ('oioioi.base.fields.EnumField', [], {'default': "'?'", 'max_length': '64'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        u'contests.submissionreport': {
            'Meta': {'ordering': "('-creation_date',)", 'object_name': 'SubmissionReport', 'index_together': "(('submission', 'creation_date'),)"},
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('oioioi.base.fields.EnumField', [], {'default': "'FINAL'", 'max_length': '64'}),
            'status': ('oioioi.base.fields.EnumField', [], {'default': "'INACTIVE'", 'max_length': '64'}),
            'submission': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contests.Submission']"})
        },
        u'problems.problem': {
            'Meta': {'object_name': 'Problem'},
            'contest': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contests.Contest']", 'null': 'True', 'blank': 'True'}),
            'controller_name': ('oioioi.base.fields.DottedNameField', [], {'max_length': '255', 'superclass': "'oioioi.problems.controllers.ProblemController'"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'package_backend_name': ('oioioi.base.fields.DottedNameField', [], {'max_length': '255', 'null': 'True', 'superclass': "'oioioi.problems.package.ProblemPackageBackend'", 'blank': 'True'}),
            'short_name': ('django.db.models.fields.CharField', [], {'max_length': '30'})
        },
        u'programs.compilationreport': {
            'Meta': {'object_name': 'CompilationReport'},
            'compiler_output': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('oioioi.base.fields.EnumField', [], {'max_length': '64'}),
            'submission_report': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contests.SubmissionReport']"})
        },
        u'programs.groupreport': {
            'Meta': {'object_name': 'GroupReport'},
            'group': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'score': ('oioioi.contests.fields.ScoreField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'status': ('oioioi.base.fields.EnumField', [], {'max_length': '64'}),
            'submission_report': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contests.SubmissionReport']"})
        },
        u'programs.modelprogramsubmission': {
            'Meta': {'object_name': 'ModelProgramSubmission', '_ormbases': [u'programs.ProgramSubmission']},
            'model_solution': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['programs.ModelSolution']"}),
            u'programsubmission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['programs.ProgramSubmission']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'programs.modelsolution': {
            'Meta': {'object_name': 'ModelSolution'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('oioioi.base.fields.EnumField', [], {'max_length': '64'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'order_key': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'problem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['problems.Problem']"}),
            'source_file': ('oioioi.filetracker.fields.FileField', [], {'max_length': '100'})
        },
        u'programs.outputchecker': {
            'Meta': {'object_name': 'OutputChecker'},
            'exe_file': ('oioioi.filetracker.fields.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'problem': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['problems.Problem']", 'unique': 'True'})
        },
        u'programs.programsubmission': {
            'Meta': {'object_name': 'ProgramSubmission', '_ormbases': [u'contests.Submission']},
            'source_file': ('oioioi.filetracker.fields.FileField', [], {'max_length': '100'}),
            'source_length': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            u'submission_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': u"orm['contests.Submission']", 'unique': 'True', 'primary_key': 'True'})
        },
        u'programs.test': {
            'Meta': {'ordering': "['order']", 'object_name': 'Test'},
            'group': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'input_file': ('oioioi.filetracker.fields.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'kind': ('oioioi.base.fields.EnumField', [], {'max_length': '64'}),
            'max_score': ('django.db.models.fields.IntegerField', [], {'default': '10'}),
            'memory_limit': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'output_file': ('oioioi.filetracker.fields.FileField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'problem': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['problems.Problem']"}),
            'time_limit': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        u'programs.testreport': {
            'Meta': {'object_name': 'TestReport'},
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'score': ('oioioi.contests.fields.ScoreField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'status': ('oioioi.base.fields.EnumField', [], {'max_length': '64'}),
            'submission_report': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contests.SubmissionReport']"}),
            'test': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['programs.Test']", 'null': 'True', 'on_delete': 'models.SET_NULL', 'blank': 'True'}),
            'test_group': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'test_max_score': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'test_name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'test_time_limit': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'time_used': ('django.db.models.fields.IntegerField', [], {'blank': 'True'})
        }
    }

    complete_apps = ['programs']