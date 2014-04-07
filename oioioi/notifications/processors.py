from django.utils.functional import lazy
from oioioi.contests.utils import can_enter_contest
from django.conf import settings
from django.template.loader import render_to_string


def notification_processor(request):
    if not getattr(request, 'contest', None):
        return {}
    if not request.user.is_authenticated():
        return {}
    if not can_enter_contest(request):
        return {}

    def generator():
        return render_to_string('notifications/notifications.html',
                                dict(notif_server_url=
                                     settings.NOTIFICATIONS_SERVER_URL))
    return {'extra_navbar_right_notifications': lazy(generator, unicode)()}
