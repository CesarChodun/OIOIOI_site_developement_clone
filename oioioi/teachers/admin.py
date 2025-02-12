from django.shortcuts import redirect
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.forms.models import modelform_factory
from oioioi.base import admin
from oioioi.base.permissions import is_superuser
from oioioi.contests.admin import ContestAdmin
from oioioi.teachers.forms import TeacherContestForm
from oioioi.teachers.menu import teacher_menu_registry
from oioioi.teachers.models import Teacher, ContestTeacher, \
        RegistrationConfig
from functools import partial


class TeacherAdmin(admin.ModelAdmin):
    list_display = ['user', 'school', 'is_active']
    list_editable = ['is_active']

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return self.has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return self.has_add_permission(request)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == 'user':
            kwargs['queryset'] = User.objects.all().order_by('username')
        return super(TeacherAdmin, self) \
                .formfield_for_foreignkey(db_field, request, **kwargs)

    def get_list_select_related(self):
        return super(TeacherAdmin, self).get_list_select_related() + ['user']

admin.site.register(Teacher, TeacherAdmin)

admin.system_admin_menu_registry.register('teachers', _("Teachers"),
        lambda request: reverse('oioioiadmin:teachers_teacher_changelist'),
        condition=is_superuser, order=20)


class ContestAdminMixin(object):
    def has_add_permission(self, request):
        if request.user.has_perm('teachers.teacher'):
            return True
        return super(ContestAdminMixin, self).has_add_permission(request)

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.controller_name = \
                    'oioioi.teachers.controllers.TeacherContestController'
        super(ContestAdminMixin, self).save_model(request, obj, form, change)
        if not change and request.user.has_perm('teachers.teacher'):
            try:
                teacher_obj = Teacher.objects.get(user=request.user)
                ContestTeacher.objects.get_or_create(contest=obj,
                        teacher=teacher_obj)
                RegistrationConfig.objects.get_or_create(contest=obj)
            except Teacher.DoesNotExist:
                pass

    def get_fieldsets(self, request, obj=None):
        if obj or request.user.is_superuser:
            return super(ContestAdminMixin, self).get_fieldsets(request, obj)
        fields = TeacherContestForm().base_fields.keys()
        return [(None, {'fields': fields})]

    def get_form(self, request, obj=None, **kwargs):
        if obj or request.user.is_superuser:
            return super(ContestAdminMixin, self).get_form(request, obj,
                    **kwargs)
        return modelform_factory(self.model, form=TeacherContestForm,
                formfield_callback=partial(self.formfield_for_dbfield,
                    request=request))

    def response_add(self, request, obj, post_url_continue='../%s/'):
        if request.user.is_superuser:
            return super(ContestAdminMixin, self).response_add(request, obj,
                    post_url_continue)
        self.message_user(request, _("Contest added successfully."))
        return redirect('oioioi.teachers.views.pupils_view',
                contest_id=obj.id)

    def __init__(self, *args, **kwargs):
        super(ContestAdminMixin, self).__init__(*args, **kwargs)

ContestAdmin.mix_in(ContestAdminMixin)

teacher_menu_registry.register('create_contest', _("New contest"),
        lambda request: reverse('oioioiadmin:contests_contest_add'),
        order=10)
