from django.utils.translation import ugettext_lazy as _
from oioioi.contests.models import Contest

from oioioi.teachers.models import Teacher, ContestTeacher


class TeacherAuthBackend(object):
    description = _("Teachers permissions")
    supports_authentication = False

    def authenticate(self, **kwargs):
        return None

    def has_perm(self, user_obj, perm, obj=None):
        if not user_obj.is_authenticated() or not user_obj.is_active:
            return False
        if perm == 'teachers.teacher':
            return bool(Teacher.objects.filter(user=user_obj, is_active=True))
        if perm == 'contests.contest_admin' and isinstance(obj, Contest):
            if not hasattr(user_obj, '_teacher_perms_cache'):
                user_obj._teacher_perms_cache = set(ContestTeacher.objects
                    .filter(teacher__user=user_obj, teacher__is_active=True)
                    .values_list('contest', flat=True))
            return obj.id in user_obj._teacher_perms_cache
