import urllib

from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.template.response import TemplateResponse
from django.http import Http404, HttpResponseRedirect
from django.core.exceptions import PermissionDenied
from django.utils.safestring import mark_safe
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _

from oioioi.problems.models import ProblemStatement, ProblemAttachment
from oioioi.filetracker.utils import stream_file
from oioioi.problems.models import Problem
from oioioi.problems.utils import can_change_problem
from oioioi.problems.problem_sources import problem_sources
from oioioi.contests.models import ProblemInstance
from oioioi.contests.utils import is_contest_admin


def show_statement_view(request, statement_id):
    statement = get_object_or_404(ProblemStatement, id=statement_id)
    if not request.user.has_perm('problems.problem_admin', statement.problem):
        raise PermissionDenied
    return stream_file(statement.content)


def show_problem_attachment_view(request, attachment_id):
    attachment = get_object_or_404(ProblemAttachment, id=attachment_id)
    if not request.user.has_perm('problems.problem_admin', attachment.problem):
        raise PermissionDenied
    return stream_file(attachment.content)


def add_or_update_problem_view(request, contest_id=None):
    sources = problem_sources(request)
    if 'key' not in request.GET:
        qs = request.GET.dict()
        qs['key'] = sources[0].key
        return HttpResponseRedirect(request.path + '?' + urllib.urlencode(qs))
    key = request.GET['key']
    for s in sources:
        if s.key == key:
            current_source = s
            break
    else:
        raise Http404

    contest = contest_id and request.contest

    if 'problem' in request.GET:
        existing_problem = \
                get_object_or_404(Problem, id=request.GET['problem'])
        if contest and not existing_problem.probleminstance_set.filter(
                contest=contest).exists():
            raise Http404
        if not can_change_problem(request, existing_problem):
            raise PermissionDenied
    else:
        existing_problem = None
        if not request.user.has_perm('problems.problems_db_admin'):
            if not contest_id:
                raise PermissionDenied
            if not is_contest_admin(request):
                raise PermissionDenied

    problem_or_content = current_source.view(request, contest,
            existing_problem)

    if isinstance(problem_or_content, Problem):
        problem = problem_or_content
        if not problem.package_backend_name:
            raise AssertionError("Problem package source (%r) did not "
                    "set Problem.package_backend_name. This is a bug in "
                    "the problem package backend." % (current_source,))
        if contest:
            if not existing_problem:
                problem.contest = contest
                problem.save()
            pi, created = ProblemInstance.objects.get_or_create(
                    problem=problem, contest=contest,
                    submissions_limit=contest.default_submissions_limit)
            if not pi.round:
                if contest.round_set.count() == 1:
                    pi.round = contest.round_set.get()
                    pi.save()
                else:
                    messages.info(request, _("Please select the round for "
                        "this problem."))
                    return redirect(
                            'oioioiadmin:contests_probleminstance_change',
                            pi.id)
            return redirect('oioioiadmin:contests_probleminstance_changelist')
        else:
            return redirect('oioioiadmin:problems_problem_changelist')

    if isinstance(problem_or_content, TemplateResponse):
        content = problem_or_content.render().content
    else:
        content = problem_or_content

    sources_context = []
    qs = request.GET.dict()
    for s in sources:
        qs['key'] = s.key
        link = request.path + '?' + urllib.urlencode(qs)
        sources_context.append({'obj': s, 'link': link})

    context = {
        'sources': sources_context,
        'current_source': current_source,
        'content': mark_safe(force_unicode(content)),
        'existing_problem': existing_problem,
    }
    return TemplateResponse(request, 'problems/add_or_update.html', context)
