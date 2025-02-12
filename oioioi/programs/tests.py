import os

from django.test import TestCase
from django.utils.html import strip_tags, escape
from django.core.urlresolvers import reverse

from oioioi.filetracker.tests import TestStreamingMixin
from oioioi.programs import utils
from oioioi.base.tests import check_not_accessible
from oioioi.contests.models import Submission, ProblemInstance, Contest
from oioioi.contests.tests import PrivateRegistrationController
from oioioi.programs.models import Test, ModelSolution, ProgramSubmission
from oioioi.programs.controllers import ProgrammingContestController
from oioioi.sinolpack.tests import get_test_filename
from oioioi.contests.scores import IntegerScore
from oioioi.base.utils import memoized_property


# Don't Repeat Yourself.
# Serves for both TestProgramsViews and TestProgramsXssViews
def extract_code(show_response):
    # Current version of pygments generates two <pre> tags,
    # first for line numeration, second for code.
    preFirst = show_response.content.find('</pre>') + 6
    preStart = show_response.content.find('<pre>', preFirst) + 5
    preEnd = show_response.content.find('</pre>', preFirst)
    # Get substring and strip tags.
    show_response.content = strip_tags(
        show_response.content[preStart:preEnd]
    )


class TestProgramsViews(TestCase, TestStreamingMixin):
    fixtures = ['test_users', 'test_contest', 'test_full_package',
            'test_submission']

    def test_submission_views(self):
        self.client.login(username='test_user')
        submission = Submission.objects.get(pk=1)
        kwargs = {'contest_id': submission.problem_instance.contest.id,
                'submission_id': submission.id}
        # Download shown response.
        show_response = self.client.get(reverse('show_submission_source',
            kwargs=kwargs))
        self.assertEqual(show_response.status_code, 200)
        # Download plain text response.
        download_response = self.client.get(reverse(
            'download_submission_source', kwargs=kwargs))
        # Extract code from <pre>'s
        extract_code(show_response)
        # Shown code has entities like &gt; - let's escape the plaintext.
        download_response_content = \
            escape(self.streamingContent(download_response))
        # Now it should work.
        self.assertEqual(download_response.status_code, 200)
        self.assertTrue(download_response.streaming)
        self.assertEqual(show_response.content, download_response_content)
        self.assertIn('main()', show_response.content)
        self.assertTrue(show_response.content.strip().endswith('}'))
        self.assertTrue(download_response['Content-Disposition'].startswith(
            'attachment'))

    def test_test_views(self):
        self.client.login(username='test_admin')
        test = Test.objects.get(name='0')
        kwargs = {'test_id': test.id}
        response = self.client.get(reverse('download_input_file',
            kwargs=kwargs))
        self.assertStreamingEqual(response, '1 2\n')
        response = self.client.get(reverse('download_output_file',
            kwargs=kwargs))
        self.assertStreamingEqual(response, '3\n')

    def test_submissions_permissions(self):
        submission = Submission.objects.get(pk=1)
        test = Test.objects.get(name='0')
        for view in ['show_submission_source', 'download_submission_source']:
            check_not_accessible(self, view, kwargs={
                'contest_id': submission.problem_instance.contest.id,
                'submission_id': submission.id})
        check_not_accessible(self, 'source_diff', kwargs={
            'contest_id': submission.problem_instance.contest.id,
            'submission1_id': submission.id,
            'submission2_id': submission.id})
        for view in ['download_input_file', 'download_output_file']:
            check_not_accessible(self, view, kwargs={'test_id': test.id})
        self.client.login(user='test_user')
        for view in ['download_input_file', 'download_output_file']:
            check_not_accessible(self, view, kwargs={'test_id': test.id})

    def test_model_solutions_view(self):
        pi = ProblemInstance.objects.get()
        ModelSolution.objects.recreate_model_submissions(pi)
        url = reverse('oioioiadmin:contests_probleminstance_models',
                args=(pi.id,))
        self.client.login(username='test_admin')
        response = self.client.get(url)
        for element in ['>sum<', '>sum1<', '>sumb0<', '>sums1<', '>100<',
                '>0<']:
            self.assertIn(element, response.content)
        self.assertEqual(response.content.count('subm_status subm_INI_OK'), 1)
        self.assertEqual(response.content.count('subm_status subm_INI_ERR'), 1)
        self.assertEqual(response.content.count('subm_status subm_OK'), 7)
        self.assertEqual(response.content.count('subm_status subm_WA'), 5)
        self.assertEqual(response.content.count('subm_status subm_CE'), 2)
        self.assertEqual(response.content.count('>10.00s<'), 5)


class TestProgramsXssViews(TestCase, TestStreamingMixin):
    fixtures = ['test_users', 'test_contest', 'test_full_package',
            'test_submission_xss']

    def test_submission_xss_views(self):
        self.client.login(username='test_user')
        submission = Submission.objects.get(pk=1)
        kwargs = {'contest_id': submission.problem_instance.contest.id,
                'submission_id': submission.id}
        # Download shown response.
        show_response = self.client.get(reverse('show_submission_source',
            kwargs=kwargs))
        # Download plain text response.
        download_response = self.client.get(reverse(
            'download_submission_source', kwargs=kwargs))
        # Get code from diff view
        diff_response = self.client.get(reverse('source_diff',
            kwargs={'contest_id': submission.problem_instance.contest.id,
                    'submission1_id': submission.id,
                    'submission2_id': submission.id}))
        # Response status before extract_code
        self.assertEqual(show_response.status_code, 200)
        self.assertEqual(diff_response.status_code, 200)
        # Extract code from <pre>'s
        extract_code(show_response)
        extract_code(diff_response)
        # Shown code has entities like &gt; - let's escape the plaintext.
        download_response_content = \
            escape(self.streamingContent(download_response))
        # Now it should work.
        self.assertEqual(download_response.status_code, 200)
        self.assertTrue(download_response.streaming)
        self.assertEqual(show_response.content, download_response_content)
        self.assertEqual(show_response.content.find('<script>'), -1)
        self.assertEqual(diff_response.content.find('<script>'), -1)
        self.assertEqual(download_response_content.find('<script>'), -1)
        self.assertIn('main()', show_response.content)
        self.assertIn('main()', diff_response.content)
        self.assertTrue(show_response.content.strip().endswith('}'))
        self.assertTrue(diff_response.content.strip().endswith('}'))
        self.assertTrue(download_response['Content-Disposition'].startswith(
            'attachment'))


class TestOtherSubmissions(TestCase):
    fixtures = ['test_users', 'test_contest', 'test_full_package',
            'test_submission', 'test_submissions_CE']

    def _test_get(self, username):
        self.client.login(username=username)
        submission = Submission.objects.get(pk=1)
        kwargs = {'contest_id': submission.problem_instance.contest.id,
                'submission_id': submission.id}
        response = self.client.get(reverse('submission', kwargs=kwargs))
        self.assertEqual(response.status_code, 200)
        self.assertIn('other-submissions', response.content)
        self.assertIn('subm_status subm_OK', response.content)
        self.assertIn('subm_status subm_CE', response.content)

    def test_admin(self):
        self._test_get('test_admin')

    def test_user(self):
        self._test_get('test_user')


class TestNoOtherSubmissions(TestCase):
    fixtures = ['test_users', 'test_contest', 'test_full_package',
            'test_submission']

    def _test_get(self, username):
        self.client.login(username=username)
        submission = Submission.objects.get(pk=1)
        kwargs = {'contest_id': submission.problem_instance.contest.id,
                'submission_id': submission.id}
        response = self.client.get(reverse('submission', kwargs=kwargs))
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('other-submissions', response.content)
        self.assertIn('subm_status subm_OK', response.content)

    def test_admin(self):
        self._test_get('test_admin')

    def test_user(self):
        self._test_get('test_user')


class TestDiffView(TestCase):
    fixtures = ['test_users', 'test_contest', 'test_full_package',
            'test_submission', 'test_another_submission']

    def test_saving_button(self):
        self.client.login(username='test_admin')
        submission = Submission.objects.get(pk=1)
        submission2 = Submission.objects.get(pk=2)
        kwargs = {'contest_id': submission.problem_instance.contest.id,
                  'submission_id': submission.id}
        response = self.client.get(reverse('submission', kwargs=kwargs))
        self.assertContains(response, 'id="diff-button-save"')
        response = self.client.get(reverse('save_diff_id', kwargs=kwargs))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('submission', kwargs=kwargs))
        self.assertContains(response, 'id="diff-button-do"')
        kwargs2 = {'contest_id': submission.problem_instance.contest.id,
                   'submission1_id': submission2.id,
                   'submission2_id': submission.id}
        self.assertIn(reverse('source_diff', kwargs=kwargs2),
                response.content)
        response = self.client.get(reverse('source_diff', kwargs=kwargs2))
        self.assertEqual(response.status_code, 200)
        response = self.client.get(reverse('submission', kwargs=kwargs))
        self.assertContains(response, 'id="diff-button-save"')

    def test_diff_view(self):
        self.client.login(username='test_admin')
        submission1 = Submission.objects.get(pk=1)
        submission2 = Submission.objects.get(pk=2)
        kwargs = {'contest_id': submission1.problem_instance.contest.id,
                  'submission1_id': submission1.id,
                  'submission2_id': submission2.id}
        kwargsrev = {'contest_id': submission1.problem_instance.contest.id,
                     'submission1_id': submission2.id,
                     'submission2_id': submission1.id}
        response = self.client.get(reverse('source_diff', kwargs=kwargs))
        self.assertContains(response, reverse('source_diff', kwargs=kwargsrev))
        self.assertIn('diff-line left', response.content)
        self.assertIn('diff-line right', response.content)
        self.assertIn('diff-num left', response.content)
        self.assertIn('diff-num right', response.content)


class TestSubmissionAdmin(TestCase):
    fixtures = ['test_users', 'test_contest', 'test_full_package',
            'test_submission']

    def test_submissions_changelist(self):
        self.client.login(username='test_admin')
        pi = ProblemInstance.objects.get()
        ModelSolution.objects.recreate_model_submissions(pi)
        url = reverse('oioioiadmin:contests_submission_changelist')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('(sum.c)', response.content)
        self.assertIn('test_user', response.content)
        self.assertIn('subm_status subm_OK', response.content)
        self.assertIn('submission_diff_action', response.content)


class TestSubmittingAsAdmin(TestCase):
    fixtures = ['test_users', 'test_contest', 'test_full_package']

    def test_ignored_submission(self):
        self.client.login(username='test_user')
        contest = Contest.objects.get()
        pi = ProblemInstance.objects.get()
        url = reverse('submit', kwargs={'contest_id': contest.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('IGNORED', response.content)

        self.client.login(username='test_admin')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('IGNORED', response.content)

        data = {
            'problem_instance_id': pi.id,
            'file': open(get_test_filename('sum-various-results.cpp'), 'rb'),
            'user': 'test_user',
            'kind': 'IGNORED'
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Submission.objects.count(), 1)
        submission = Submission.objects.get(pk=1)
        self.assertEqual(submission.user.username, 'test_user')
        self.assertEqual(submission.kind, 'IGNORED')

        url = reverse('default_ranking', kwargs={'contest_id': contest.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Test User', response.content)

        self.client.login(username='test_user')
        url = reverse('my_submissions', kwargs={'contest_id': contest.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('(Ignored)', response.content)

    def test_submitting_as_self(self):
        self.client.login(username='test_admin')
        contest = Contest.objects.get()
        pi = ProblemInstance.objects.get()
        url = reverse('submit', kwargs={'contest_id': contest.id})

        self.client.login(username='test_admin')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('IGNORED', response.content)
        self.assertIn('NORMAL', response.content)

        f = open(get_test_filename('sum-various-results.cpp'), 'rb')
        data = {
            'problem_instance_id': pi.id,
            'file': f,
            'user': 'test_admin',
            'kind': 'NORMAL'
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Submission.objects.count(), 1)
        submission = Submission.objects.get(pk=1)
        self.assertEqual(submission.user.username, 'test_admin')
        self.assertEqual(submission.kind, 'NORMAL')

        ps = ProgramSubmission.objects.get(pk=1)
        f.seek(0, os.SEEK_END)
        self.assertEqual(ps.source_length, f.tell())

        url = reverse('default_ranking', kwargs={'contest_id': contest.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Test Admin', response.content)
        self.assertIn('no one in this ranking', response.content)


class PrivateProgrammingContestController(ProgrammingContestController):
    def registration_controller(self):
        return PrivateRegistrationController(self.contest)


class TestSubmittingAsContestAdmin(TestCase):
    fixtures = ['test_users', 'test_contest', 'test_full_package',
            'test_permissions']

    def test_missing_permission(self):
        contest = Contest.objects.get()
        contest.controller_name = \
                'oioioi.programs.tests.PrivateProgrammingContestController'
        contest.save()
        pi = ProblemInstance.objects.get()
        url = reverse('submit', kwargs={'contest_id': contest.id})

        self.client.login(username='test_contest_admin')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('IGNORED', response.content)

        data = {
            'problem_instance_id': pi.id,
            'file': open(get_test_filename('sum-various-results.cpp'), 'rb'),
            'user': 'test_user',
            'kind': 'NORMAL'
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Submission.objects.count(), 0)
        self.assertIn('enough privileges', response.content)


class TestSubmittingAsObserver(TestCase):
    fixtures = ['test_users', 'test_contest', 'test_full_package',
            'test_permissions']

    def test_ignored_submission(self):
        self.client.login(username='test_observer')
        contest = Contest.objects.get()
        pi = ProblemInstance.objects.get()
        url = reverse('submit', kwargs={'contest_id': contest.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('IGNORED', response.content)

        data = {
            'problem_instance_id': pi.id,
            'file': open(get_test_filename('sum-various-results.cpp'), 'rb'),
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Submission.objects.count(), 1)
        submission = Submission.objects.get(pk=1)
        self.assertEqual(submission.user.username, 'test_observer')
        self.assertEqual(submission.kind, 'IGNORED')

        url = reverse('default_ranking', kwargs={'contest_id': contest.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('Test Observer', response.content)

        url = reverse('my_submissions', kwargs={'contest_id': contest.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('(Ignored)', response.content)


class TestScorers(TestCase):
    t_results_ok = (
        ({'exec_time_limit': 100, 'max_score': 100},
            {'result_code': 'OK', 'time_used': 0}),
        ({'exec_time_limit': 100, 'max_score': 100},
            {'result_code': 'OK', 'time_used': 50}),
        ({'exec_time_limit': 1000, 'max_score': 100},
            {'result_code': 'OK', 'time_used': 501}),
        ({'exec_time_limit': 100, 'max_score': 100},
            {'result_code': 'OK', 'time_used': 75}),
        ({'exec_time_limit': 1000, 'max_score': 100},
            {'result_code': 'OK', 'time_used': 999}),
        ({'max_score': 100},
            {'result_code': 'OK', 'time_used': 0}),
        ({'max_score': 100},
            {'result_code': 'OK', 'time_used': 99999}),
        )

    t_results_ok_perc = (
        ({'exec_time_limit': 100, 'max_score': 100},
            {'result_code': 'OK', 'time_used': 0, 'result_percentage': 99}),
        ({'exec_time_limit': 100, 'max_score': 100},
            {'result_code': 'OK', 'time_used': 75, 'result_percentage': 50}),
        ({'exec_time_limit': 100, 'max_score': 100},
            {'result_code': 'OK', 'time_used': 75, 'result_percentage': 0}),
        )

    t_results_unequal_max_scores = (
        ({'exec_time_limit': 100, 'max_score': 10},
            {'result_code': 'OK', 'time_used': 10}),
        ({'exec_time_limit': 1000, 'max_score': 20},
            {'result_code': 'WA', 'time_used': 50}),
        )

    t_expected_unequal_max_scores = [
        (IntegerScore(10), IntegerScore(10), 'OK'),
        (IntegerScore(0), IntegerScore(20), 'WA'),
        ]

    t_results_wrong = [
        ({'exec_time_limit': 100, 'max_score': 100},
            {'result_code': 'WA', 'time_used': 75}),
        ({'exec_time_limit': 100, 'max_score': 100},
            {'result_code': 'RV', 'time_used': 75}),
        ]

    t_expected_wrong = [
        (IntegerScore(0), IntegerScore(100), 'WA'),
        (IntegerScore(0), IntegerScore(100), 'RV'),
        ]

    def test_discrete_test_scorer(self):
        exp_scores = [100] * len(self.t_results_ok)
        exp_max_scores = [100] * len(self.t_results_ok)
        exp_statuses = ['OK'] * len(self.t_results_ok)
        expected = zip(exp_scores, exp_max_scores, exp_statuses)

        results = map(utils.discrete_test_scorer, *zip(*self.t_results_ok))
        self.assertEquals(expected, results)

        results = map(utils.discrete_test_scorer, *zip(*self.t_results_wrong))
        self.assertEquals(self.t_expected_wrong, results)

        results = map(utils.discrete_test_scorer,
                *zip(*self.t_results_unequal_max_scores))
        self.assertEquals(self.t_expected_unequal_max_scores, results)

    def test_threshold_linear_test_scorer(self):
        exp_scores = [100, 100, 99, 50, 0, 100, 100]
        exp_max_scores = [100] * len(self.t_results_ok)
        exp_statuses = ['OK'] * len(self.t_results_ok)
        expected = zip(exp_scores, exp_max_scores, exp_statuses)

        results = map(utils.threshold_linear_test_scorer,
                        *zip(*self.t_results_ok))
        self.assertEquals(expected, results)

        exp_scores = [99, 25, 0]
        exp_max_scores = [100] * len(self.t_results_ok_perc)
        exp_statuses = ['OK'] * len(self.t_results_ok_perc)
        expected = zip(exp_scores, exp_max_scores, exp_statuses)

        results = map(utils.threshold_linear_test_scorer,
                        *zip(*self.t_results_ok_perc))
        self.assertEquals(expected, results)

        malformed = ({'exec_time_limit': 100, 'max_score': 100},
                        {'result_code': 'OK', 'time_used': 101})
        self.assertEqual(utils.threshold_linear_test_scorer(*malformed),
                        (0, 100, 'TLE'))

        results = map(utils.threshold_linear_test_scorer,
                        *zip(*self.t_results_wrong))
        self.assertEquals(self.t_expected_wrong, results)

        results = map(utils.threshold_linear_test_scorer,
                        *zip(*self.t_results_unequal_max_scores))
        self.assertEquals(self.t_expected_unequal_max_scores, results)

    @memoized_property
    def g_results_ok(self):
        # Tested elsewhere
        results = map(utils.threshold_linear_test_scorer,
                        *zip(*self.t_results_ok[:4]))
        dicts = [dict(score=sc.serialize(), max_score=msc.serialize(),
                status=st) for sc, msc, st in results]
        return dict(zip(xrange(len(dicts)), dicts))

    @memoized_property
    def g_results_wrong(self):
        results = map(utils.threshold_linear_test_scorer,
                        *zip(*self.t_results_wrong))
        dicts = self.g_results_ok.values()
        dicts += [dict(score=sc.serialize(), max_score=msc.serialize(),
                status=st) for sc, msc, st in results]
        return dict(zip(xrange(len(dicts)), dicts))

    @memoized_property
    def g_results_unequal_max_scores(self):
        results = map(utils.threshold_linear_test_scorer,
                        *zip(*self.t_results_unequal_max_scores))
        dicts = self.g_results_wrong.values()
        dicts += [dict(score=sc.serialize(), max_score=msc.serialize(),
                status=st) for sc, msc, st in results]
        return dict(zip(xrange(len(dicts)), dicts))

    def test_min_group_scorer(self):
        self.assertEqual((50, 100, 'OK'),
                utils.min_group_scorer(self.g_results_ok))
        self.assertEqual((0, 100, 'WA'),
                utils.min_group_scorer(self.g_results_wrong))
        with self.assertRaises(utils.UnequalMaxScores):
            utils.min_group_scorer(self.g_results_unequal_max_scores)

    def test_sum_group_scorer(self):
        self.assertEqual((349, 400, 'OK'),
                utils.sum_group_scorer(self.g_results_ok))
        self.assertEqual((349, 600, 'WA'),
                utils.sum_group_scorer(self.g_results_wrong))
        self.assertEqual((359, 630, 'WA'),
                utils.sum_group_scorer(self.g_results_unequal_max_scores))

    def test_sum_score_aggregator(self):
        self.assertEqual((349, 400, 'OK'),
                utils.sum_score_aggregator(self.g_results_ok))
        self.assertEqual((349, 600, 'WA'),
                utils.sum_score_aggregator(self.g_results_wrong))
        self.assertEqual((359, 630, 'WA'),
                utils.sum_score_aggregator(self.g_results_unequal_max_scores))
