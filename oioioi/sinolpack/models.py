import yaml

from django.db import models
from django.utils.translation import ugettext_lazy as _

from oioioi.problems.models import Problem, make_problem_filename
from oioioi.filetracker.fields import FileField


class ExtraConfig(models.Model):
    """Model to store ``config.yml`` present in some Sinol packages."""
    problem = models.OneToOneField(Problem)
    config = models.TextField(verbose_name=_("config"))

    @property
    def parsed_config(self):
        if not self.config:
            return {}
        return yaml.load(self.config)

    class Meta(object):
        verbose_name = _("sinolpack's configuration")
        verbose_name_plural = _("sinolpack's configurations")


class ExtraFile(models.Model):
    """Model to store extra files (for example ``extra.zip``) present in some
       Sinol packages."""
    problem = models.ForeignKey(Problem)
    name = models.CharField(max_length=255, verbose_name=_("name"))
    file = FileField(upload_to=make_problem_filename)

    class Meta(object):
        verbose_name = _("sinolpack's extra file")
        verbose_name_plural = _("sinolpack's extra files")


class OriginalPackage(models.Model):
    problem = models.ForeignKey(Problem)
    package_file = FileField(upload_to=make_problem_filename,
            verbose_name=_("package"))

    class Meta(object):
        verbose_name = _("original sinolpack package")
        verbose_name_plural = _("original sinolpack packages")
