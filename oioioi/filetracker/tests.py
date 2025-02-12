from django.utils import unittest
from django.test import TestCase
from django.core.urlresolvers import reverse
from django.core.files.base import ContentFile
from django.db.models.fields.files import FieldFile, FileField
from django.core.files.storage import default_storage
from oioioi.filetracker.models import TestFileModel
from oioioi.filetracker.storage import FiletrackerStorage
from oioioi.filetracker.utils import django_to_filetracker_path, \
        filetracker_to_django_file
import filetracker
import filetracker.dummy

import tempfile
import shutil
import datetime


class TestFileField(TestCase):
    def test_file_field(self):
        f = ContentFile('eloziom', name='foo')

        model = TestFileModel()
        model.file_field = f
        model.save()
        pk = model.pk

        # Here the model is removed from Django's cache, so the query
        # below actually hits the database.
        del model

        model = TestFileModel.objects.get(pk=pk)
        self.assertEqual(model.file_field.read(), 'eloziom')

        model.file_field.delete()

    def test_filetracker_to_django_field(self):
        data = 'eloziom'
        path = 'my/path'
        abspath = '/' + path

        storage = default_storage
        try:
            self.assertEqual(storage.save(path, ContentFile(data)), path)

            model = TestFileModel()
            # File field is ignoring preferred name, as we can't copy file
            # in filetracker to another location
            with self.assertRaises(NotImplementedError):
                model.file_field.save('xx',
                        filetracker_to_django_file(abspath, storage))

            model.file_field = filetracker_to_django_file(abspath, storage)
            model.save()
            self.assertEqual(model.file_field.name, path)
            pk = model.pk

            # Here the model is removed from Django's cache, so the query
            # below actually hits the database.
            del model

            model = TestFileModel.objects.get(pk=pk)
            self.assertEqual(model.file_field.name, path)
            self.assertEqual(django_to_filetracker_path(model.file_field),
                                abspath)
            self.assertEqual(model.file_field.read(), data)
        finally:
            default_storage.delete(path)

    def test_django_to_filetracker_path(self):
        storage = FiletrackerStorage(prefix='/foo',
                client=filetracker.dummy.DummyClient())
        field = FileField(storage=storage)
        value = FieldFile(None, field, 'bar')
        self.assertEqual(django_to_filetracker_path(value), '/foo/bar')

        with self.assertRaises(ValueError):
            django_to_filetracker_path(ContentFile('whatever', name='gizmo'))

        self.assertEqual('/foo/bar', django_to_filetracker_path(
                filetracker_to_django_file('/foo/bar', storage=storage)))


class TestFileStorage(unittest.TestCase):
    def _test_file_storage(self, storage):
        data = 'eloziom'
        path = 'my/path'

        with self.assertRaises(ValueError):
            storage.save('/absolute/path', ContentFile(data))

        storage.save(path, ContentFile(data))
        t = datetime.datetime.now()
        self.assert_(storage.exists(path))
        self.assertEqual(storage.open(path, 'rb').read(), data)
        self.assertEqual(storage.size(path), len(data))

        ctime = storage.created_time(path)
        self.assertLessEqual(ctime, t)
        self.assertGreater(ctime, t - datetime.timedelta(seconds=30))

        storage.delete(path)
        self.assert_(not storage.exists(path))
        with self.assertRaises(Exception):
            storage.open(path, 'rb')

    def test_dummy_file_storage(self):
        storage = FiletrackerStorage()
        self._test_file_storage(storage)

    def test_real_file_storage(self):
        dir = tempfile.mkdtemp()
        try:
            client = filetracker.Client(cache_dir=dir, remote_store=None)
            storage = FiletrackerStorage(client=client)
            self._test_file_storage(storage)
        finally:
            shutil.rmtree(dir)


class TestStreamingMixin(object):
    def assertStreamingEqual(self, response, content):
        self.assertEqual(self.streamingContent(response), content)

    def streamingContent(self, response):
        self.assertTrue(response.streaming)
        return ''.join(response.streaming_content)


class TestFileStorageViews(TestCase, TestStreamingMixin):
    fixtures = ['test_users']

    def test_raw_file_view(self):
        filename = 'tests/test_raw_file_view.txt'
        content = 'foo'
        default_storage.save(filename, ContentFile(content))
        try:
            url = reverse('oioioi.filetracker.views.raw_file_view',
                    kwargs={'filename': filename})
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403)
            self.client.login(username='test_user')
            response = self.client.get(url)
            self.assertEqual(response.status_code, 403)
            self.client.login(username='test_admin')
            response = self.client.get(url)
            self.assertStreamingEqual(response, content)
        finally:
            default_storage.delete(filename)


class TestFileFixtures(TestCase):
    fixtures = ['test_file_field']

    def test_file_fixtures(self):
        instance = TestFileModel.objects.get()
        self.assertEqual(instance.file_field.name, 'tests/test_file_field.txt')
        self.assertEqual(instance.file_field.read(), 'whatever\x01\xff')
