from django import forms
from django.utils.translation import ugettext_lazy as _
from oioioi.publicsolutions.utils import \
    problem_instances_with_any_public_solutions


class FilterPublicSolutionsForm(forms.Form):
    category = forms.ChoiceField([], label=_("Problem"), required=False)

    def __init__(self, request, *args, **kwargs):
        super(FilterPublicSolutionsForm, self).__init__(*args, **kwargs)
        pis = problem_instances_with_any_public_solutions(request)
        choices = [(pi.id, pi) for pi in pis]

        choices.insert(0, ('', _("All")))

        self.fields['category'].choices = choices
