import re
import time
from datetime import datetime

import pytz
from django.contrib import messages
from django.http import Http404
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from oioioi.base.utils.redirect import safe_redirect

from oioioi.contests.models import Round
from oioioi.status import status_registry
from oioioi.su.utils import is_real_superuser


@status_registry.register
def get_times_status(request, response):
    """Extends the response dictionary with rounds times.

       Extends the dictionary with keys:
       ``time``: the number of seconds elapsed since the epoch
       ``round_start_date``: the number of seconds between the epoch
       and the start of the current round if any exists; otherwise 0
       ``round_end_date`` the number of seconds between the epoch
       and the end of the current round if any exists; otherwise 0
       ``is_admin_time_set``: ``True`` if admin changes the time
    """
    timestamp = getattr(request, 'timestamp', None)
    contest = getattr(request, 'contest', None)
    response.update(dict(time=0, round_start_date=0, round_end_date=0,
        is_time_admin=False, is_admin_time_set=False))

    if getattr(request, 'real_user', None) and is_real_superuser(request):
        response['is_time_admin'] = True
        response['sync_time'] = min(10000, response.get('sync_time', 10000))

    next_rounds_times = None
    current_rounds_times = None

    if timestamp and contest:
        rtimes = [contest.controller.get_round_times(request, round)
                    for round in Round.objects.filter(contest=contest)]
        next_rounds_times = [rt for rt in rtimes if rt.is_future(timestamp)]
        next_rounds_times.sort(key=lambda rt: rt.get_start())
        current_rounds_times = [rt for rt in rtimes
                                if rt.is_active(timestamp) and rt.get_end()]
        current_rounds_times.sort(key=lambda rt: rt.get_end())

    if current_rounds_times:
        response['round_start_date'] = time.mktime((timezone
            .localtime(current_rounds_times[0].get_start())).timetuple())
        response['round_end_date'] = time.mktime((timezone
            .localtime(current_rounds_times[0].get_end())).timetuple())
    elif next_rounds_times:
        response['round_start_date'] = time.mktime((timezone
            .localtime(next_rounds_times[0].get_start())).timetuple())

    if 'admin_time' in request.session:
        response['is_admin_time_set'] = True
        clock_time = timestamp
    else:
        clock_time = timezone.now()

    response['time'] = time.mktime(timezone.localtime(clock_time).timetuple())

    return response


def admin_time(request, next_page=None):
    if 'next' in request.REQUEST:
        next_page = request.REQUEST['next']

    if request.method == 'POST':
        if 'reset-button' in request.POST:
            if 'admin_time' in request.session:
                del request.session['admin_time']
            return safe_redirect(request, next_page)
        elif is_real_superuser(request):
            current_admin_time = re.findall(r'\d+', request.POST['admin-time'])
            current_admin_time = map(int, current_admin_time)
            try:
                current_admin_time = datetime(*current_admin_time)
            except (ValueError, TypeError, OverflowError):
                messages.error(request,
                    _("Invalid date. Admin-time was not set."))
                return safe_redirect(request, next_page)
            if current_admin_time.year >= 1900:
                request.session['admin_time'] = \
                    timezone.localtime(timezone.now()). \
                    tzinfo.localize(current_admin_time).astimezone(pytz.utc)
            else:
                messages.error(request, _("Date has to be after 1900."
                    " Admin-time was not set."))
            return safe_redirect(request, next_page)
    raise Http404
