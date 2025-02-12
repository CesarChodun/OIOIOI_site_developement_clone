from django.utils.translation import ugettext_lazy as _
from django.core.urlresolvers import reverse
from django.contrib.admin import SimpleListFilter
from django.utils.encoding import force_unicode
from django.db import transaction

from oioioi.base import admin
from oioioi.base.admin import system_admin_menu_registry
from oioioi.base.utils import make_html_link
from oioioi.contests.menu import contest_admin_menu_registry
from oioioi.submitsqueue.models import QueuedSubmit


class UserListFilter(SimpleListFilter):
    title = _("user")
    parameter_name = 'user'

    def lookups(self, request, model_admin):
        users = list(set(QueuedSubmit.objects
                         .filter(submission__problem_instance__contest=
                                 request.contest)
                         .values_list('submission__user__id',
                                      'submission__user__username')))
        if (None, None) in users:
            users = [x for x in users if x != (None, None)]
            users.append(('None', _("(None)")))
        return users

    def queryset(self, request, queryset):
        if self.value():
            if self.value() != 'None':
                return queryset.filter(submission__user=self.value())
            else:
                return queryset.filter(submission__user=None)
        else:
            return queryset


class ProblemNameListFilter(SimpleListFilter):
    title = _("problem")
    parameter_name = 'pi'

    def lookups(self, request, model_admin):
        # Unique problem names
        p_names = list(set(QueuedSubmit.objects
                           .filter(submission__problem_instance__contest=
                                   request.contest)
                           .values_list(
                               'submission__problem_instance__problem__name',
                               flat=True)))
        return [(x, x) for x in p_names]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(
                submission__problem_instance__problem__name=self.value())
        else:
            return queryset


class SystemSubmitsQueueAdmin(admin.ModelAdmin):
    list_display = ['submit_id', 'colored_state', 'contest',
                    'problem_instance', 'user', 'creation_date',
                    'celery_task_id']
    list_filter = ['state', ProblemNameListFilter]
    actions = ['remove_from_queue', 'delete_selected']

    def __init__(self, *args, **kwargs):
        super(SystemSubmitsQueueAdmin, self).__init__(*args, **kwargs)
        self.list_display_links = (None, )

    def _get_link(self, caption, app, **kwargs):
        url = reverse(app, kwargs=kwargs)
        return make_html_link(url, caption)

    def _get_contest_id(self, instance):
        return instance.submission.problem_instance.contest.id

    def has_add_permission(self, request):
        return False

    def submit_id(self, instance):
        res = instance.submission.id
        return self._get_link(res, 'submission',
                              contest_id=self._get_contest_id(instance),
                              submission_id=res)
    submit_id.allow_tags = True
    submit_id.admin_order_field = 'submission__id'
    submit_id.short_description = _("Submission id")

    def problem_instance(self, instance):
        res = instance.submission.problem_instance
        return self._get_link(res, 'problem_statement',
                              contest_id=self._get_contest_id(instance),
                              problem_instance=res.short_name)
    problem_instance.allow_tags = True
    problem_instance.admin_order_field = 'submission__problem_instance'
    problem_instance.short_description = _("Problem")

    def contest(self, instance):
        return self._get_link(instance.submission.problem_instance.contest,
                              'default_contest_view',
                              contest_id=self._get_contest_id(instance))
    contest.allow_tags = True
    contest.admin_order_field = 'submission__problem_instance__contest'
    contest.short_description = _("Contest")

    def user(self, instance):
        return instance.submission.user
    user.admin_order_field = 'submission__user'
    user.short_description = _("User")

    def colored_state(self, instance):
        subm_state = 'in_progress'
        if instance.state == 'QUEUED':
            subm_state = 'queued'
        return '<span class="subm_admin subm_%s">%s</span>' % \
            (subm_state, force_unicode(instance.get_state_display()))
    colored_state.allow_tags = True
    colored_state.short_description = _("Status")
    colored_state.admin_order_field = 'state'

    @transaction.commit_on_success
    def remove_from_queue(self, request, queryset):
        for obj in queryset:
            obj.state = 'CANCELLED'
            obj.save()
    remove_from_queue.short_description = \
        _("Remove selected submissions from the queue")

    def queryset(self, request):
        qs = super(SystemSubmitsQueueAdmin, self).queryset(request)
        return qs.exclude(state='CANCELLED')

    def has_delete_permission(self, request, obj=None):
        return True

    def get_list_select_related(self):
        return super(SystemSubmitsQueueAdmin, self) \
            .get_list_select_related() + [
                    'submission__problem_instance',
                    'submission__problem_instance__contest',
                    'submission__problem_instance__problem',
                    'submission__user']


admin.site.register(QueuedSubmit, SystemSubmitsQueueAdmin)
system_admin_menu_registry.register('queuedsubmit_admin',
        _("Evaluation queue"), lambda request: reverse(
            'oioioiadmin:submitsqueue_queuedsubmit_changelist'),
        order=60)


class ContestQueuedSubmit(QueuedSubmit):
    class Meta(object):
        proxy = True
        verbose_name = _("Contest Queued Submit")


class ContestSubmitsQueueAdmin(SystemSubmitsQueueAdmin):
    def __init__(self, *args, **kwargs):
        super(ContestSubmitsQueueAdmin, self).__init__(*args, **kwargs)
        self.list_display = [x for x in self.list_display if x != 'contest']
        self.list_filter = self.list_filter + [UserListFilter]

    def queryset(self, request):
        qs = super(ContestSubmitsQueueAdmin, self).queryset(request)
        return qs.filter(submission__problem_instance__contest=request.contest)


admin.site.register(ContestQueuedSubmit, ContestSubmitsQueueAdmin)
contest_admin_menu_registry.register('queuedsubmit_admin',
        _("Evaluation queue"), lambda request: reverse(
            'oioioiadmin:submitsqueue_contestqueuedsubmit_changelist'),
        condition=(lambda request: not request.user.is_superuser),
        order=60)
