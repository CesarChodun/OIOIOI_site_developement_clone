from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.utils.text import capfirst
from django.utils.translation import ugettext_lazy as _, ungettext_lazy
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from oioioi.base import admin
from oioioi.contests.admin import RoundTimeExtensionAdmin
from oioioi.base.permissions import make_request_condition
from oioioi.contests.menu import contest_admin_menu_registry
from oioioi.participants.forms import ParticipantForm, ExtendRoundForm
from oioioi.participants.models import Participant
from oioioi.contests.models import RoundTimeExtension
from oioioi.participants.utils import contest_has_participants
from oioioi.contests.utils import is_contest_admin


@make_request_condition
def has_participants_admin(request):
    rcontroller = request.contest.controller.registration_controller()
    return getattr(rcontroller, 'participant_admin', None) is not None


class ParticipantAdmin(admin.ModelAdmin):
    list_select_related = True
    list_display = ['user_login', 'user_full_name', 'status']
    list_filter = ['status', ]
    fields = [('user', 'status'), ]
    search_fields = ['user__username', 'user__last_name']
    actions = ['make_active', 'make_banned', 'delete_selected', 'extend_round']
    form = ParticipantForm

    def has_add_permission(self, request):
        return is_contest_admin(request)

    def has_change_permission(self, request, obj=None):
        return is_contest_admin(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_change_permission(request, obj)

    def user_login(self, instance):
        if not instance.user:
            return ''
        return instance.user.username
    user_login.short_description = _("Login")
    user_login.admin_order_field = 'user__username'

    def user_full_name(self, instance):
        if not instance.user:
            return ''
        return instance.user.get_full_name()
    user_full_name.short_description = _("User name")
    user_full_name.admin_order_field = 'user__last_name'

    def get_list_select_related(self):
        return super(ParticipantAdmin, self).get_list_select_related() \
                + ['user']

    def queryset(self, request):
        qs = super(ParticipantAdmin, self).queryset(request)
        qs = qs.filter(contest=request.contest)
        return qs

    def save_model(self, request, obj, form, change):
        obj.contest = request.contest
        obj.save()

    def get_form(self, request, obj=None, **kwargs):
        Form = super(ParticipantAdmin, self).get_form(request, obj, **kwargs)

        def form_wrapper(*args, **kwargs):
            form = Form(*args, **kwargs)
            form.request_contest = request.contest
            return form
        return form_wrapper

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            kwargs['queryset'] = User.objects.all().order_by('username')
        return super(ParticipantAdmin, self) \
                .formfield_for_foreignkey(db_field, request, **kwargs)

    def make_active(self, request, queryset):
        queryset.update(status='ACTIVE')
    make_active.short_description = _("Mark selected participants as active")

    def make_banned(self, request, queryset):
        queryset.update(status='BANNED')
    make_banned.short_description = _("Mark selected participants as banned")

    def extend_round(self, request, queryset):
        form = None

        if 'submit' in request.POST:
            form = ExtendRoundForm(request.contest, request.POST)

            if form.is_valid():
                round = form.cleaned_data['round']
                extra_time = form.cleaned_data['extra_time']

                users = [participant.user for participant in queryset]
                existing_extensions = RoundTimeExtension.objects \
                        .filter(round=round, user__in=users)
                for extension in existing_extensions:
                    extension.extra_time += extra_time
                    extension.save()
                existing_count = existing_extensions.count()

                new_extensions = [RoundTimeExtension(user=user, round=round,
                        extra_time=extra_time) for user in users
                        if not existing_extensions.filter(user=user).exists()]
                RoundTimeExtension.objects.bulk_create(new_extensions)

                if existing_count:
                    if existing_count > 1:
                        name = capfirst(
                            RoundTimeExtension._meta.verbose_name_plural)
                    else:
                        name = RoundTimeExtension._meta.verbose_name
                    self.message_user(request, ungettext_lazy(
                        "Updated one %(name)s.",
                        "%(name)s updated: %(existing_count)d.",
                        existing_count
                    ) % {'existing_count': existing_count, 'name': name})
                if new_extensions:
                    if len(new_extensions) > 1:
                        name = capfirst(
                            RoundTimeExtension._meta.verbose_name_plural)
                    else:
                        name = RoundTimeExtension._meta.verbose_name
                    self.message_user(request, ungettext_lazy(
                        "Created one %(name)s.",
                        "%(name)s created: %(new_count)d.",
                        len(new_extensions)
                    ) % {'new_count': len(new_extensions), 'name': name})

                return HttpResponseRedirect(request.get_full_path())

        if not form:
            form = ExtendRoundForm(request.contest,
                    initial={'_selected_action': [p.id for p in queryset]})

        return TemplateResponse(request,
                                'admin/participants/extend_round.html',
                                {'form': form})
    extend_round.short_description = _("Extend round")


class NoParticipantAdmin(ParticipantAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class ContestDependentParticipantAdmin(admin.InstanceDependentAdmin):
    default_participant_admin = NoParticipantAdmin

    def _find_model_admin(self, request, object_id):
        rcontroller = request.contest.controller.registration_controller()
        if has_participants_admin(request):
            participant_admin = rcontroller.participant_admin(self.model,
                                                              self.admin_site)
        else:
            participant_admin = self.default_participant_admin(self.model,
                                                               self.admin_site)
        return participant_admin

    def _model_admin_for_instance(self, request, instance=None):
        raise NotImplementedError

admin.site.register(Participant, ContestDependentParticipantAdmin)
contest_admin_menu_registry.register('participants', _("Participants"),
    lambda request: reverse('oioioiadmin:participants_participant_changelist'),
    condition=has_participants_admin, order=30)


class ParticipantInline(admin.TabularInline):
    model = Participant
    extra = 0
    readonly_fields = ('contest', 'status')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        # Protected by parent ModelAdmin
        return True

    def has_delete_permission(self, request, obj=None):
        return False


class UserWithParticipantsAdminMixin(object):
    def __init__(self, *args, **kwargs):
        super(UserWithParticipantsAdminMixin, self).__init__(*args, **kwargs)
        self.inlines = self.inlines + [ParticipantInline]
admin.OioioiUserAdmin.mix_in(UserWithParticipantsAdminMixin)


class ParticipantsRoundTimeExtensionMixin(object):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            if contest_has_participants(request):
                kwargs['queryset'] = User.objects \
                    .filter(id__in=Participant.objects
                        .filter(contest=request.contest)
                        .values_list('user', flat=True)) \
                    .order_by('username')
        return super(ParticipantsRoundTimeExtensionMixin, self) \
            .formfield_for_foreignkey(db_field, request, **kwargs)
RoundTimeExtensionAdmin.mix_in(ParticipantsRoundTimeExtensionMixin)
