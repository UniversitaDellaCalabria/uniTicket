from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.forms import ModelForm
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext as _

from django_form_builder.dynamic_fields import CustomFileField
from organizational_area.models import (OrganizationalStructure,
                                        OrganizationalStructureOffice,
                                        OrganizationalStructureOfficeEmployee,)

from . models import *
from . utils import *
# from . widgets import UniTicketSelectSearchWidget
from bootstrap_italia_template.widgets import BootstrapItaliaSelectWidget


class CategoryForm(ModelForm):
    class Meta:
        model = TicketCategory
        fields = ['name', 'description',
                  'show_heading_text', 'allow_guest', 'allow_user', 'allow_employee']
        labels = {'name': _('Nome'),
                  'description': _('Descrizione'),}
    class Media:
        js = ('js/textarea-autosize.js',)


class CategoryAddOfficeForm(forms.Form):
    office = forms.ModelChoiceField(label=_('Assegna competenza ufficio'),
                                    queryset=None, required=True,
                                    widget=BootstrapItaliaSelectWidget())
    def __init__(self, *args, **kwargs):
        structure = kwargs.pop('structure', None)
        offices = OrganizationalStructureOffice.objects.filter(organizational_structure=structure,
                                                               is_active=True)
        super().__init__(*args, **kwargs)
        self.fields['office'].queryset = offices
        self.fields['office'].to_field_name = 'slug'

    class Media:
        js = ('js/textarea-autosize.js',)


class CategoryInputModuleForm(ModelForm):
    class Meta:
        model = TicketCategoryModule
        fields = ['name']
        labels = {'name': _('Nome')}


class CategoryInputListForm(ModelForm):
    class Meta:
        model = TicketCategoryInputList
        fields = ['name', 'field_type', 'valore',
                  'is_required', 'aiuto', 'ordinamento']
        labels = {'name': _('Nome'),
                  'is_required': _('Obbligatorio'),
                  'field_type': _('Tipologia di campo'),}
        widgets = {'input_type': BootstrapItaliaSelectWidget()}


class ChiusuraForm(forms.Form):
    note = forms.CharField(label=_('Motivazione'),
                           widget=forms.Textarea,
                           required=True)

    class Media:
        js = ('js/textarea-autosize.js',)


class OfficeForm(ModelForm):
    """
    """
    class Meta:
        model = OrganizationalStructureOffice
        fields = ['name', 'description']
        labels = {'name': _('Nome'),
                  'description': _('Descrizione'),}

    class Media:
        js = ('js/textarea-autosize.js',)


class OfficeAddOperatorForm(forms.Form):
    operatore = forms.ModelChoiceField(label=_('Assegna operatore'),
                                       queryset=None, required=True,
                                       widget=BootstrapItaliaSelectWidget())
    description = forms.CharField(label=_('Note'),
                                  widget=forms.Textarea(),
                                  required=False)
    def __init__(self, *args, **kwargs):
        structure = kwargs.pop('structure', None)
        office_slug = kwargs.pop('office_slug', '')
        # current_user = kwargs.pop('current_user', None)
        osoe = OrganizationalStructureOfficeEmployee
        actual = []
        actual_employees = osoe.objects.filter(office__slug=office_slug)
        for ae in actual_employees:
            # if ae.employee.pk not in actual:
            actual.append(ae.employee.pk)
        # all employees in a structure
        # DISTINCT ON (.distinct(field_name) is not supported by all datablase backends)
        # all_employees = osoe.objects.filter(office__organizational_structure=structure).distinct('employee')
        all_employees = osoe.objects.filter(office__organizational_structure=structure)
        # exclude employees already assigned to office
        clean_list = all_employees.exclude(employee__pk__in=actual)
        operators_ids = []
        for operator_office in clean_list:
            key = operator_office.employee.pk
            if key not in operators_ids:
                operators_ids.append(key)
        operators = get_user_model().objects.filter(pk__in=operators_ids)
        super().__init__(*args, **kwargs)
        self.fields['operatore'].queryset = operators

    class Media:
        js = ('js/textarea-autosize.js',)


class PriorityForm(forms.Form):
    priorita = forms.ChoiceField(choices=settings.PRIORITY_LEVELS,
                                 required=True,
                                 initial=0,
                                 label=_('Priorità'),
                                 widget=BootstrapItaliaSelectWidget())


class ReplyForm(forms.Form):
    subject = forms.CharField(label=_('Oggetto'), required=True)
    text = forms.CharField(label=_('Testo'),
                           required=True,
                           widget=forms.Textarea())
    attachment = CustomFileField(label=_('Allegato'), required=False)

    class Media:
        js = ('js/textarea-autosize.js',)


class TicketCompetenceForm(forms.Form):
    structures = forms.ModelChoiceField(queryset=None, required=True,
                                        widget=BootstrapItaliaSelectWidget())
    offices = forms.ModelChoiceField(queryset=None, required=True,
                                     widget=BootstrapItaliaSelectWidget())
    def __init__(self, *args, **kwargs):
        structure_slug = kwargs.pop('structure_slug', None)
        current_ticket_id = kwargs.pop('ticket_id', None)
        ticket_dependences_code_list = kwargs.pop('ticket_dependences', [])
        structure = OrganizationalStructure.objects.get(slug=structure_slug)
        ticket_id_list = TicketAssignment.get_ticket_per_structure(structure)
        ticket_id_list.remove(current_ticket_id)
        ticket_list = Ticket.objects.filter(code__in=ticket_id_list,
                                            # is_taken=True,
                                            is_closed=False).exclude(code__in=ticket_dependences_code_list)
        result_list = ticket_list
        for ticket in ticket_list:
            if not ticket.has_been_taken():
                result_list = result_list.exclude(pk=ticket.pk)
        super().__init__(*args, **kwargs)
        self.fields['ticket'].queryset = result_list
        self.fields['ticket'].to_field_name='code'


class TicketCompetenceSchemeForm(forms.Form):
    """
    Build a form scheme to have cleaned data submitted
    from competence transfer final step,
    even if this is not passed to template
    (rendered manually to have js behaviour)
    """
    # structure_slug = forms.CharField(label=_('Struttura'), required=True)
    category_slug = forms.CharField(label=_('Categoria'), required=True)
    follow = forms.BooleanField(label=_('Continua a seguire'), required=False)
    readonly = forms.BooleanField(label=_('Sola lettura'), required=False)


class TicketDependenceForm(forms.Form):
    """
    """
    ticket = forms.ModelChoiceField(queryset=None, required=True,
                                    widget=BootstrapItaliaSelectWidget())
    note = forms.CharField(label=_('Note'),
                           widget=forms.Textarea,
                           required=True)

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        structure = kwargs.pop('structure', None)
        current_ticket_id = kwargs.pop('ticket_id', None)
        ticket_dependences_code_list = kwargs.pop('ticket_dependences', [])
        ticket_id_list = []
        # if user is manager/default_office operator:
        # he views all tickets followed by structure offices
        if user_is_manager(user, structure) or user_is_in_default_office(user, structure):
            ticket_id_list = TicketAssignment.get_ticket_per_structure(structure)
        # if user is operator:
        # he views all tickets followed in his offices
        else:
            user_offices = user_is_operator(user, structure)
            offices_list = user_offices_list(user_offices)
            ticket_id_list = TicketAssignment.get_ticket_in_office_list(offices_list)
        ticket_id_list.remove(current_ticket_id)
        cleaned_list = [code for code in ticket_id_list if code not in ticket_dependences_code_list]
        ticket_list = Ticket.objects.filter(code__in=cleaned_list,
                                            is_closed=False)
        result_list = ticket_list
        for ticket in ticket_list:
            if not ticket.has_been_taken():
                result_list = result_list.exclude(pk=ticket.pk)
        super().__init__(*args, **kwargs)
        self.fields['ticket'].queryset = result_list
        self.fields['ticket'].to_field_name='code'

    class Media:
        js = ('js/textarea-autosize.js',)


class TaskForm(forms.Form):
    subject = forms.CharField(label=_('Oggetto'), required=True)
    description = forms.CharField(label=_('Testo'),
                                  required=True,
                                  widget=forms.Textarea())
    priority = forms.ChoiceField(choices=settings.PRIORITY_LEVELS,
                                 required=True,
                                 initial=0,
                                 label=_('Priorità'),)
    attachment = CustomFileField(label=_('Allegato'), required=False)

    class Media:
        js = ('js/textarea-autosize.js',)


class CategoryConditionForm(ModelForm):
    class Meta:
        model = TicketCategoryCondition
        fields = ['title', 'text', 'ordinamento', 'attachment',
                  'is_printable','is_active']
        labels = {'title': _('Titolo'),
                  'text': _('Testo'),
                  'ordinamento': _('Ordinamento'),
                  'attachment': _('Allegato'),
                  'is_printable': _('Visibile nel documento di stampa'),
                  'is_active': _('Attiva'),}

    class Media:
        js = ('js/textarea-autosize.js',)


class OfficeAddCategoryForm(forms.Form):
    category = forms.ModelChoiceField(label=_('Assegna tipologia di richiesta'),
                                      queryset=None, required=True,
                                      widget=BootstrapItaliaSelectWidget())
    def __init__(self, *args, **kwargs):
        structure = kwargs.pop('structure', None)
        office = kwargs.pop('office', None)
        categories = TicketCategory.objects.filter(organizational_structure=structure).exclude(organizational_office__isnull=False)
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = categories
        self.fields['category'].to_field_name='slug'


class CategoryTaskForm(TaskForm):
    is_active = forms.BooleanField(label=_('Attiva'))
