from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from oioioi.contests.models import Contest, Round, RoundTimeExtension
from django.utils.timezone import utc
from datetime import datetime
import calendar
import json
import time


class TestClock(TestCase):
    fixtures = ['test_contest', 'test_users']

    def test_clock(self):
        response = self.client.get(reverse('get_status'))
        response = json.loads(response.content)
        response_time = response['time']
        now = time.time()
        self.assertLessEqual(response_time, now)
        self.assertGreater(response_time, now - 10)

    def test_countdown(self):
        contest = Contest.objects.get()
        now = time.time()
        r1_start = datetime.fromtimestamp(now - 5)
        r1_end = datetime.fromtimestamp(now + 10)
        r2_start = datetime.fromtimestamp(now - 10)
        r2_end = datetime.fromtimestamp(now + 5)
        r1 = Round(contest=contest, start_date=r1_start, end_date=r1_end)
        r2 = Round(contest=contest, start_date=r2_start, end_date=r2_end)
        r1.save()
        r2.save()

        response = self.client.get(reverse('get_contest_status',
            kwargs={'contest_id': contest.id}))
        response = json.loads(response.content)
        round_start_date = response['round_start_date']
        round_end_date = response['round_end_date']
        self.assertEqual(round_start_date, time.mktime(r2_start.timetuple()))
        self.assertEqual(round_end_date, time.mktime(r2_end.timetuple()))

    def test_countdown_with_extended_rounds(self):
        contest = Contest.objects.get()
        now = time.time()
        r1_start = datetime.fromtimestamp(now - 5)
        r1_end = datetime.fromtimestamp(now + 10)
        r1 = Round(contest=contest, start_date=r1_start, end_date=r1_end)
        r1.save()
        user = User.objects.get(username='test_user')
        RoundTimeExtension(user=user, round=r1, extra_time=10).save()

        self.client.login(username='test_user')
        response = self.client.get(reverse('get_contest_status',
            kwargs={'contest_id': contest.id}))
        response = json.loads(response.content)
        round_start_date = response['round_start_date']
        round_end_date = response['round_end_date']
        self.assertEqual(round_start_date, time.mktime(r1_start.timetuple()))
        self.assertEqual(round_end_date, time.mktime(r1_end.timetuple()) + 600)

    def test_admin_time(self):
        self.client.login(username='test_admin')
        session = self.client.session
        session['admin_time'] = datetime(2012, 12, 12, tzinfo=utc)
        session.save()
        response = self.client.get(reverse('get_status'))
        response = json.loads(response.content)
        self.assertTrue(response['is_admin_time_set'])
        self.assertEqual(response['time'],
            calendar.timegm(session['admin_time'].timetuple()))
