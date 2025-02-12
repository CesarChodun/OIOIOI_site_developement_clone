# coding: utf-8

from django.test import TestCase
from django.core.management import call_command
from django.core.urlresolvers import reverse
from oioioi.filetracker.tests import TestStreamingMixin
from oioioi.sinolpack.package import SinolPackageBackend, \
        DEFAULT_TIME_LIMIT
from oioioi.contests.models import ProblemInstance, Contest, \
        Submission, UserResultForContest
from oioioi.contests.scores import IntegerScore
from oioioi.problems.models import Problem, ProblemStatement
from oioioi.programs.models import Test, OutputChecker, ModelSolution, \
        TestReport
from oioioi.sinolpack.models import ExtraConfig, ExtraFile
from nose.plugins.attrib import attr
from nose.tools import nottest
import os.path
from cStringIO import StringIO
import urllib
import zipfile


@nottest
def get_test_filename(name):
    return os.path.join(os.path.dirname(__file__), 'files', name)


# Fixes error "no such table: nose_c" as described in
# https://github.com/jbalogh/django-nose/issues/15#issuecomment-1033686
Test._meta.get_all_related_objects()
TestReport._meta.get_all_related_objects()
ModelSolution._meta.get_all_related_objects()


class TestSinolPackage(TestCase):
    fixtures = ['test_users', 'test_contest']

    def test_identify_zip(self):
        filename = get_test_filename('test_simple_package.zip')
        self.assert_(SinolPackageBackend().identify(filename))

    def test_identify_tgz(self):
        filename = get_test_filename('test_full_package.tgz')
        self.assert_(SinolPackageBackend().identify(filename))

    def _check_no_ingen_package(self, problem, doc=True):
        self.assertEqual(problem.short_name, 'test')

        tests = Test.objects.filter(problem=problem)
        t0 = tests.get(name='0')
        self.assertEqual(t0.input_file.read(), '0 0\n')
        self.assertEqual(t0.output_file.read(), '0\n')
        self.assertEqual(t0.kind, 'EXAMPLE')
        self.assertEqual(t0.group, '0')
        self.assertEqual(t0.max_score, 0)
        self.assertEqual(t0.time_limit, 10000)
        self.assertEqual(t0.memory_limit, 66000)
        t1a = tests.get(name='1a')
        self.assertEqual(t1a.input_file.read(), '0 0\n')
        self.assertEqual(t1a.output_file.read(), '0\n')
        self.assertEqual(t1a.kind, 'NORMAL')
        self.assertEqual(t1a.group, '1')
        self.assertEqual(t1a.max_score, 100)
        self.assertEqual(t1a.time_limit, 10000)
        self.assertEqual(t1a.memory_limit, 66000)
        t1b = tests.get(name='1b')
        self.assertEqual(t1b.input_file.read(), '0 0\n')
        self.assertEqual(t1b.output_file.read(), '0\n')
        self.assertEqual(t1b.kind, 'NORMAL')
        self.assertEqual(t1b.group, '1')
        self.assertEqual(t1b.max_score, 100)
        self.assertEqual(t1b.time_limit, 10000)
        self.assertEqual(t1b.memory_limit, 66000)

        model_solutions = ModelSolution.objects.filter(problem=problem)
        sol = model_solutions.get(name='test.c')
        self.assertEqual(sol.kind, 'NORMAL')
        self.assertEqual(model_solutions.count(), 1)

    def test_no_ingen_package(self):
        filename = get_test_filename('test_no_ingen_package.tgz')
        call_command('addproblem', filename)
        problem = Problem.objects.get()
        self._check_no_ingen_package(problem)

        # Rudimentary test of package updating
        call_command('updateproblem', str(problem.id), filename)
        problem = Problem.objects.get()
        self._check_no_ingen_package(problem)

    def _check_full_package(self, problem, doc=True):
        self.assertEqual(problem.short_name, 'sum')

        config = ExtraConfig.objects.get(problem=problem)
        assert 'extra_compilation_args' in config.parsed_config

        if doc:
            self.assertEqual(problem.name, u'Sumżyce')
            statements = ProblemStatement.objects.filter(problem=problem)
            self.assertEqual(statements.count(), 1)
            self.assert_(statements.get().content.read().startswith('%PDF'))
        else:
            self.assertEqual(problem.name, u'sum')

        tests = Test.objects.filter(problem=problem)
        t0 = tests.get(name='0')
        self.assertEqual(t0.input_file.read(), '1 2\n')
        self.assertEqual(t0.output_file.read(), '3\n')
        self.assertEqual(t0.kind, 'EXAMPLE')
        self.assertEqual(t0.group, '0')
        self.assertEqual(t0.max_score, 0)
        self.assertEqual(t0.time_limit, DEFAULT_TIME_LIMIT)
        self.assertEqual(t0.memory_limit, 133000)
        t1a = tests.get(name='1a')
        self.assertEqual(t1a.kind, 'NORMAL')
        self.assertEqual(t1a.group, '1')
        self.assertEqual(t1a.max_score, 33)
        t1b = tests.get(name='1b')
        self.assertEqual(t1b.kind, 'NORMAL')
        self.assertEqual(t1b.group, '1')
        self.assertEqual(t1b.max_score, 33)
        self.assertEqual(t1b.time_limit, 100)
        t1ocen = tests.get(name='1ocen')
        self.assertEqual(t1ocen.kind, 'EXAMPLE')
        self.assertEqual(t1ocen.group, '1ocen')
        self.assertEqual(t1ocen.max_score, 0)
        t2 = tests.get(name='2')
        self.assertEqual(t2.kind, 'NORMAL')
        self.assertEqual(t2.group, '2')
        self.assertEqual(t2.max_score, 33)
        t3 = tests.get(name='3')
        self.assertEqual(t3.kind, 'NORMAL')
        self.assertEqual(t3.group, '3')
        self.assertEqual(t3.max_score, 34)
        self.assertEqual(tests.count(), 6)

        checker = OutputChecker.objects.get(problem=problem)
        self.assertIsNotNone(checker.exe_file)

        extra_files = ExtraFile.objects.filter(problem=problem)
        self.assertEqual(extra_files.count(), 1)
        self.assertEqual(extra_files.get().name, 'makra.h')

        model_solutions = \
            ModelSolution.objects.filter(problem=problem).order_by('order_key')
        sol = model_solutions.get(name='sum.c')
        self.assertEqual(sol.kind, 'NORMAL')
        sol1 = model_solutions.get(name='sum1.pas')
        self.assertEqual(sol1.kind, 'NORMAL')
        sols1 = model_solutions.get(name='sums1.cpp')
        self.assertEqual(sols1.kind, 'SLOW')
        solb0 = model_solutions.get(name='sumb0.c')
        self.assertEqual(solb0.kind, 'INCORRECT')
        self.assertEqual(model_solutions.count(), 4)
        self.assertEqual(list(model_solutions), [sol, sol1, sols1, solb0])

        tests = Test.objects.filter(problem=problem)

    @attr('slow')
    def test_full_unpack_update(self):
        filename = get_test_filename('test_full_package.tgz')
        call_command('addproblem', filename)
        problem = Problem.objects.get()
        self._check_full_package(problem)

        # Rudimentary test of package updating
        call_command('updateproblem', str(problem.id), filename)
        problem = Problem.objects.get()
        self._check_full_package(problem)

    @attr('slow')
    def test_huge_unpack_update(self):
        self.client.login(username='test_admin')
        filename = get_test_filename('test_huge_package.tgz')
        call_command('addproblem', filename)
        problem = Problem.objects.get()

        # Rudimentary test of package updating
        url = reverse('add_or_update_problem') + '?' + \
              urllib.urlencode({'problem': problem.id})
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        url = response.redirect_chain[-1][0]
        response = self.client.post(url,
            {'package_file': open(filename, 'rb')}, follow=True)
        self.assertEqual(response.status_code, 200)
        url = reverse('oioioiadmin:problems_problem_changelist')
        print response.content
        self.assertRedirects(response, url)

    def test_title_in_config_yml(self):
        filename = get_test_filename('test_simple_package.zip')
        call_command('addproblem', filename)
        problem = Problem.objects.get()
        self.assertEqual(problem.name, 'Testowe')

    def test_title_from_doc(self):
        filename = get_test_filename('test_simple_package_no_config.zip')
        call_command('addproblem', filename)
        problem = Problem.objects.get()
        self.assertNotEqual(problem.name, 'Not this one')
        self.assertEqual(problem.name, 'Testowe')

    def test_latin2_title(self):
        filename = get_test_filename('test_simple_package_latin2.zip')
        call_command('addproblem', filename)
        problem = Problem.objects.get()
        self.assertEqual(problem.name, u'Łąka')

    def test_utf8_title(self):
        filename = get_test_filename('test_simple_package_utf8.zip')
        call_command('addproblem', filename)
        problem = Problem.objects.get()
        self.assertEqual(problem.name, u'Łąka')

    def test_memory_limit_from_doc(self):
        filename = get_test_filename('test_simple_package_no_config.zip')
        call_command('addproblem', filename)
        test = Test.objects.filter(memory_limit=132000)
        self.assertEqual(test.count(), 5)


class TestSinolPackageInContest(TestCase, TestStreamingMixin):
    fixtures = ['test_users', 'test_contest']

    def test_upload_and_download_package(self):
        ProblemInstance.objects.all().delete()

        contest = Contest.objects.get()
        filename = get_test_filename('test_simple_package.zip')
        self.client.login(username='test_admin')
        url = reverse('oioioiadmin:problems_problem_add')
        response = self.client.get(url, {'contest_id': contest.id},
                follow=True)
        url = response.redirect_chain[-1][0]
        self.assertEqual(response.status_code, 200)
        self.assertIn('problems/add_or_update.html',
                [getattr(t, 'name', None) for t in response.templates])
        response = self.client.post(url,
                {'package_file': open(filename, 'rb')}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Problem.objects.count(), 1)
        self.assertEqual(ProblemInstance.objects.count(), 1)

        # Delete tests and check if re-uploading will fix it.
        problem = Problem.objects.get()
        num_tests = problem.test_set.count()
        for test in problem.test_set.all():
            test.delete()
        problem.save()
        url = reverse('add_or_update_contest_problem',
                kwargs={'contest_id': contest.id}) + '?' + \
                        urllib.urlencode({'problem': problem.id})
        response = self.client.get(url, follow=True)
        url = response.redirect_chain[-1][0]
        self.assertEqual(response.status_code, 200)
        self.assertIn('problems/add_or_update.html',
                [getattr(t, 'name', None) for t in response.templates])
        response = self.client.post(url,
                {'package_file': open(filename, 'rb')}, follow=True)
        self.assertEqual(response.status_code, 200)
        problem = Problem.objects.get()
        self.assertEqual(problem.test_set.count(), num_tests)

        response = self.client.get(
                reverse('oioioiadmin:problems_problem_download',
                    args=(problem.id,)))
        self.assertStreamingEqual(response, open(filename, 'rb').read())


class TestSinolPackageCreator(TestCase, TestStreamingMixin):
    fixtures = ['test_users', 'test_full_package']

    def test_sinol_package_creator(self):
        problem = Problem.objects.get()
        self.client.login(username='test_admin')
        response = self.client.get(
                reverse('oioioiadmin:problems_problem_download',
                    args=(problem.id,)))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        stream = StringIO(self.streamingContent(response))
        zip = zipfile.ZipFile(stream, 'r')
        self.assertEqual(sorted(zip.namelist()), [
                'sum/doc/sumzad.pdf',
                'sum/in/sum0.in',
                'sum/in/sum1a.in',
                'sum/in/sum1b.in',
                'sum/in/sum1ocen.in',
                'sum/in/sum2.in',
                'sum/in/sum3.in',
                'sum/out/sum0.out',
                'sum/out/sum1a.out',
                'sum/out/sum1b.out',
                'sum/out/sum1ocen.out',
                'sum/out/sum2.out',
                'sum/out/sum3.out',
                'sum/prog/sum.c',
                'sum/prog/sum1.pas',
                'sum/prog/sumb0.c',
                'sum/prog/sums1.cpp',
            ])


class TestJudging(TestCase):
    fixtures = ['test_users', 'test_contest', 'test_full_package']

    def test_judging(self):
        self.client.login(username='test_user')
        contest = Contest.objects.get()
        url = reverse('submit', kwargs={'contest_id': contest.id})

        # Show submission form
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('contests/submit.html',
                [getattr(t, 'name', None) for t in response.templates])
        form = response.context['form']
        self.assertEqual(len(form.fields['problem_instance_id'].choices), 1)
        pi_id = form.fields['problem_instance_id'].choices[0][0]

        # Submit
        filename = get_test_filename('sum-various-results.cpp')
        response = self.client.post(url, {
            'problem_instance_id': pi_id, 'file': open(filename, 'rb')})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Submission.objects.count(), 1)
        self.assertEqual(TestReport.objects.count(), 6)
        self.assertEqual(TestReport.objects.filter(status='OK').count(), 4)
        self.assertEqual(TestReport.objects.filter(status='WA').count(), 1)
        self.assertEqual(TestReport.objects.filter(status='RE').count(), 1)
        submission = Submission.objects.get()
        self.assertEqual(submission.status, 'INI_OK')
        self.assertEqual(submission.score, IntegerScore(34))

        urc = UserResultForContest.objects.get()
        self.assertEqual(urc.score, IntegerScore(34))
