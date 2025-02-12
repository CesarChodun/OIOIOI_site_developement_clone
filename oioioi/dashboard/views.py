import itertools

from django.conf import settings
from django.template.response import TemplateResponse
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.template.loader import render_to_string
from django.shortcuts import redirect

from oioioi.base.menu import menu_registry
from oioioi.base.permissions import enforce_condition
from oioioi.contests.models import Submission
from oioioi.contests.controllers import submission_template_context
from oioioi.contests.utils import can_enter_contest, contest_exists, \
        has_any_submittable_problem, has_any_visible_problem_instance, \
        is_contest_admin
from oioioi.dashboard.menu import top_links_registry
from oioioi.dashboard.registry import dashboard_registry, \
        dashboard_headers_registry
from oioioi.dashboard.models import DashboardMessage
from oioioi.dashboard.forms import DashboardMessageForm
from oioioi.rankings.views import has_any_ranking_visible
from oioioi.questions.views import messages_template_context, \
        visible_messages

top_links_registry.register('problems_list', _("Problems"),
        lambda request: reverse('problems_list', kwargs={'contest_id':
            request.contest.id}),
        condition=has_any_visible_problem_instance,
        order=100)

top_links_registry.register('submit', _("Submit"),
        lambda request: reverse('submit', kwargs={'contest_id':
            request.contest.id}),
        condition=has_any_submittable_problem,
        order=200)

top_links_registry.register('ranking', _("Ranking"),
        lambda request: reverse('default_ranking', kwargs={'contest_id':
            request.contest.id}),
        condition=has_any_ranking_visible,
        order=300)


# http://stackoverflow.com/questions/1624883/alternative-way-to-split-a-list-into-groups-of-n
def grouper(n, iterable, fillvalue=None):
    "grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx"
    args = [iter(iterable)] * n
    return list(itertools.izip_longest(*args, fillvalue=fillvalue))


@enforce_condition(contest_exists & is_contest_admin)
def dashboard_message_edit_view(request, contest_id):
    instance, _created = DashboardMessage.objects.get_or_create(
            contest_id=contest_id)
    if request.method == 'POST':
        form = DashboardMessageForm(request, request.POST, instance=instance)
        if form.is_valid():
            form.save()
            return redirect('contest_dashboard', contest_id=contest_id)
    else:
        form = DashboardMessageForm(request, instance=instance)
    return TemplateResponse(request, 'dashboard/edit_dashboard_message.html',
            {'form': form})


@dashboard_registry.register_decorator(order=10)
def dashboard_message_fragment(request):
    if request.contest is None:
        return None
    try:
        instance = DashboardMessage.objects.get(contest=request.contest)
    except DashboardMessage.DoesNotExist:
        instance = None

    is_admin = is_contest_admin(request)
    content = ''
    if instance and instance.content:
        content = instance.content

    if not content and not is_admin:
        return ''

    context = {
        'content': content,
        'is_admin': is_admin,
    }
    return render_to_string('dashboard/dashboard_message.html',
        context_instance=RequestContext(request, context))


@dashboard_headers_registry.register_decorator(order=100)
def top_links_fragment(request):
    top_links = grouper(3, top_links_registry.template_context(request))
    context = {
        'top_links': top_links,
    }
    return render_to_string('dashboard/top_links.html',
        context_instance=RequestContext(request, context))


@dashboard_registry.register_decorator(order=100)
def submissions_fragment(request):
    if not request.user.is_authenticated():
        return None
    submissions = Submission.objects \
            .filter(problem_instance__contest=request.contest) \
            .order_by('-date').select_related()
    cc = request.contest.controller
    submissions = cc.filter_my_visible_submissions(request, submissions)
    submissions = \
            submissions[:getattr(settings, 'NUM_DASHBOARD_SUBMISSIONS', 8)]
    if not submissions:
        return None
    submissions = [submission_template_context(request, s)
                   for s in submissions]
    show_scores = any(s['can_see_score'] for s in submissions)
    context = {
        'submissions': submissions,
        'show_scores': show_scores
    }
    return render_to_string('dashboard/submissions.html',
        context_instance=RequestContext(request, context))


@dashboard_registry.register_decorator(order=200)
def messages_fragment(request):
    messages = messages_template_context(request, visible_messages(request))
    messages = messages[:getattr(settings, 'NUM_DASHBOARD_MESSAGES', 8)]
    if not messages:
        return None
    context = {
        'records': messages,
    }
    return render_to_string('dashboard/messages.html',
        context_instance=RequestContext(request, context))


@menu_registry.register_decorator(_("Dashboard"), lambda request:
        reverse('contest_dashboard',
                kwargs={'contest_id': request.contest.id}),
    order=20)
@enforce_condition(contest_exists & can_enter_contest)
def contest_dashboard_view(request, contest_id):
    headers = [gen(request) for gen in dashboard_headers_registry]
    headers = [hdr for hdr in headers if hdr is not None]
    fragments = [gen(request) for gen in dashboard_registry]
    fragments = [frag for frag in fragments if frag is not None]
    if not fragments:
        fragments = [render_to_string('dashboard/no_fragments.html',
            context_instance=RequestContext(request))]
    context = {
        'headers': headers,
        'fragments': fragments,
    }
    return TemplateResponse(request, 'dashboard/dashboard.html', context)
