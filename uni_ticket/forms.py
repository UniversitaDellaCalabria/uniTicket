from django import forms
from django.apps import apps
from django.conf import settings
from django.forms import ModelForm
from django.template.defaultfilters import filesizeformat
from django.utils.translation import gettext as _

from django_form_builder.dynamic_fields import CustomFileField
from django_form_builder.settings import *
from organizational_area.models import (OrganizationalStructure,
                                        OrganizationalStructureOffice,
                                        OrganizationalStructureOfficeEmployee,)

from . models import *
from . settings import PRIORITY_LEVELS
# from . widgets import UnicalSelectWidget


class CategoryForm(ModelForm):
    class Meta:
        model = TicketCategory
        fields = ['name', 'description',
                  'allow_guest', 'allow_user', 'allow_employee']
        labels = {'name': _('Nome'),
                  'description': _('Descrizione'),}
    class Media:
        js = ('js/textarea-autosize.js',)


class CategoryAddOfficeForm(forms.Form):
    office = forms.ModelChoiceField(label=_('Assegna competenza ufficio'),
                                    queryset=None, required=True,)
                                    # widget=UnicalSelectWidget())
    def __init__(self, *args, **kwargs):
        structure = kwargs.pop('structure', None)
        offices = OrganizationalStructureOffice.objects.filter(organizational_structure=structure,
                                                               is_active=True,
                                                               is_default=False)
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
        # widgets = {'input_type': UnicalSelectWidget(),}


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
                                       queryset=None, required=True,)
                                       # widget=UnicalSelectWidget())
    description = forms.CharField(label=_('Note'),
                                  widget=forms.Textarea(),
                                  required=False)
    def __init__(self, *args, **kwargs):
        structure = kwargs.pop('structure', None)
        office_slug = kwargs.pop('office_slug', None)
        current_user = kwargs.pop('current_user', None)
        osoe = OrganizationalStructureOfficeEmployee
        actual_employees = osoe.objects.filter(office__slug=office_slug)
        actual = []
        for ae in actual_employees:
            if ae.employee.pk not in actual:
                actual.append(ae.employee.pk)
        # all employees in a structure
        all_employees = osoe.objects.filter(office__organizational_structure=structure)
        # exclude employees already assigned to office
        clean_list = all_employees.exclude(employee__pk__in=actual)
        # exclude all managers from list
        for o in clean_list:
            if get_user_type(o.employee, structure)=='manager':
                clean_list = clean_list.exclude(pk=o.pk)
        unique_ids = tuple(set((i[0] for i in clean_list.values_list('employee'))))
        user_model = apps.get_model(settings.AUTH_USER_MODEL)
        operators = user_model.objects.filter(pk__in=unique_ids)
        super().__init__(*args, **kwargs)
        self.fields['operatore'].queryset = operators

    class Media:
        js = ('js/textarea-autosize.js',)


class PriorityForm(forms.Form):
    priorita = forms.ChoiceField(choices=PRIORITY_LEVELS,
                                 required=True,
                                 initial=0,
                                 label=_('Priorità'),)
                                 # widget=UnicalSelectWidget())


class ReplyForm(forms.Form):
    subject = forms.CharField(label=_('Oggetto'), required=True)
    text = forms.CharField(label=_('Testo'),
                           required=True,
                           widget=forms.Textarea())
    attachment = CustomFileField(label=_('Allegato'), required=False)

    class Media:
        js = ('js/textarea-autosize.js',)


class TicketCompetenceForm(forms.Form):
    structures = forms.ModelChoiceField(queryset=None, required=True,)
                                        # widget=UnicalSelectWidget())
    offices = forms.ModelChoiceField(queryset=None, required=True,)
                                     # widget=UnicalSelectWidget())
    def __init__(self, *args, **kwargs):
        structure_slug = kwargs.pop('structure_slug', None)
        current_ticket_id = kwargs.pop('ticket_id', None)
        ticket_dependences_code_list = kwargs.pop('ticket_dependences', None)
        structure = OrganizationalStructure.objects.get(slug=structure_slug)
        ticket_id_list = TicketAssignment.get_ticket_per_structure(structure)
        ticket_id_list.remove(current_ticket_id)
        ticket_list = Ticket.objects.filter(code__in=ticket_id_list,
                                            is_taken=True,
                                            is_closed=False).exclude(code__in=ticket_dependences_code_list)
        super().__init__(*args, **kwargs)
        self.fields['ticket'].queryset = ticket_list
        self.fields['ticket'].to_field_name='code'


class TicketDependenceForm(forms.Form):
    """
    """
    ticket = forms.ModelChoiceField(queryset=None, required=True,)
                                    # widget=UnicalSelectWidget())
    note = forms.CharField(label=_('Note'),
                           widget=forms.Textarea,
                           required=True)

    def __init__(self, *args, **kwargs):
        structure = kwargs.pop('structure', None)
        current_ticket_id = kwargs.pop('ticket_id', None)
        ticket_dependences_code_list = kwargs.pop('ticket_dependences', None)
        ticket_id_list = TicketAssignment.get_ticket_per_structure(structure)
        ticket_id_list.remove(current_ticket_id)
        ticket_list = Ticket.objects.filter(code__in=ticket_id_list,
                                            is_taken=True,
                                            is_closed=False).exclude(code__in=ticket_dependences_code_list)
        super().__init__(*args, **kwargs)
        self.fields['ticket'].queryset = ticket_list
        self.fields['ticket'].to_field_name='code'

    class Media:
        js = ('js/textarea-autosize.js',)


class TaskForm(forms.Form):
    subject = forms.CharField(label=_('Oggetto'), required=True)
    description = forms.CharField(label=_('Testo'),
                                  required=True,
                                  widget=forms.Textarea())
    priority = forms.ChoiceField(choices=PRIORITY_LEVELS,
                                 required=True,
                                 initial=0,
                                 label=_('Priorità'),)
    attachment = CustomFileField(label=_('Allegato'), required=False)

    class Media:
        js = ('js/textarea-autosize.js',)


class CategoryConditionForm(ModelForm):
    class Meta:
        model = TicketCategoryCondition
        fields = ['title', 'text', 'ordinamento',
                  'is_printable','is_active']
        labels = {'title': _('Titolo'),
                  'text': _('Descrizione'),
                  'ordinamento': _('Ordinamento'),
                  'is_printable': _('Visibile nel documento di stampa'),
                  'is_active': _('Attiva'),}

    class Media:
        js = ('js/textarea-autosize.js',)


class OfficeAddCategoryForm(forms.Form):
    category = forms.ModelChoiceField(label=_('Assegna categoria'),
                                      queryset=None, required=True,)
                                      # widget=UnicalSelectWidget())
    def __init__(self, *args, **kwargs):
        structure = kwargs.pop('structure', None)
        office = kwargs.pop('office', None)
        categories = TicketCategory.objects.filter(organizational_structure=structure).exclude(organizational_office=office)
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = categories
        self.fields['category'].to_field_name='slug'
