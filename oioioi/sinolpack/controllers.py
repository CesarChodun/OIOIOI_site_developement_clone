from django.utils.translation import ugettext_lazy as _
from oioioi.sinolpack.admin import SinolpackProblemAdminMixin
from oioioi.sinolpack.models import ExtraConfig, ExtraFile
from oioioi.programs.controllers import ProgrammingProblemController
from oioioi.filetracker.utils import django_to_filetracker_path


class SinolProblemController(ProgrammingProblemController):
    description = _("Sinol package problem")

    def fill_evaluation_environ(self, environ, **kwargs):
        super(SinolProblemController, self).fill_evaluation_environ(
                environ, **kwargs)

        try:
            config = ExtraConfig.objects.get(problem=self.problem) \
                     .parsed_config
        except ExtraConfig.DoesNotExist:
            config = {}

        lang = environ['language']
        extra_args = config.get('extra_compilation_args', {}).get(lang)
        if extra_args:
            environ['extra_compilation_args'] = extra_args

        extra_file_names = config.get('extra_compilation_files', ())
        extra_files = ExtraFile.objects.filter(problem=self.problem,
                name__in=extra_file_names).all()
        if len(extra_file_names) != len(extra_files):
            raise RuntimeError('Did not find expected extra files: '
                    + ', '.join(extra_file_names))
        environ['extra_files'] = dict(
                (ef.name, django_to_filetracker_path(ef.file))
                for ef in extra_files)

    def mixins_for_admin(self):
        return super(SinolProblemController, self).mixins_for_admin() + \
               (SinolpackProblemAdminMixin,)
