import copy

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.forms import ModelChoiceField, ModelForm
from django.template.defaultfilters import filesizeformat
from django.utils.translation import ugettext_lazy as _

from bootstrap_italia_template.widgets import (BootstrapItaliaSelectWidget,
                                               BootstrapItaliaSelectMultipleWidget)
from organizational_area.models import (OrganizationalStructure,
                                        OrganizationalStructureOffice,
                                        OrganizationalStructureOfficeEmployee,)
from uni_ticket_bootstrap_italia_template.widgets import UniTicketDateTimeWidget

from . models import *
from . utils import *


class CategoryForm(ModelForm):
    class Meta:
        model = TicketCategory
        fields = ['name', 'description',
                  'confirm_message_text',
                  'date_start',
                  'date_end',
                  'not_available_message',
                  'is_notification',
                  'show_heading_text',
                  'allow_anonymous', 'allow_guest',
                  'allow_user', 'allow_employee',
                  'user_multiple_open_tickets',
                  'allowed_users',
                  'receive_email',
                  'protocol_required']
        labels = {'name': _('Nome'),
                  'description': _('Descrizione'),
                  'allowed_users': _('Solo i seguenti utenti possono effettuare richieste')}
        widgets = {'description': forms.Textarea(attrs={'rows':2}),
                   'confirm_message_text': forms.Textarea(attrs={'rows':2}),
                   'allowed_users': BootstrapItaliaSelectMultipleWidget,
                   'date_start': UniTicketDateTimeWidget,
                   'date_end': UniTicketDateTimeWidget}
        help_texts = {'date_start': _("Formato {}. Lasciare vuoto  per non impostare"
                                      "").format(settings.DEFAULT_DATETIME_FORMAT.replace('%','')),
                      'date_end': _("Formato {}. Lasciare vuoto  per non impostare"
                                    "").format(settings.DEFAULT_DATETIME_FORMAT.replace('%',''))}

    class Media:
        js = ('js/textarea-autosize.js',)


class CategoryAddOfficeForm(forms.Form):
    office = forms.ModelChoiceField(label=_('Assegna competenza ufficio'),
                                    queryset=None, required=True,
                                    widget=BootstrapItaliaSelectWidget)
    def __init__(self, *args, **kwargs):
        structure = kwargs.pop('structure', None)
        offices = OrganizationalStructureOffice.objects.filter(organizational_structure=structure,
                                                               is_active=True)
        super().__init__(*args, **kwargs)
        self.fields['office'].queryset = offices
        self.fields['office'].to_field_name = 'slug'


class CategoryInputModuleForm(ModelForm):
    class Meta:
        model = TicketCategoryModule
        fields = ['name']
        labels = {'name': _('Nome')}


class CategoryInputListForm(ModelForm):
    class Meta:
        model = TicketCategoryInputList
        fields = ['field_type', 'name', 'valore', 'pre_text',
                  'aiuto', 'is_required', 'ordinamento']
        labels = {'name': _('Denominazione'),
                  'field_type': _('Tipo di campo'),
                  'pre_text': _('Testo statico (Pre-text)'),
                  'valore': _('Definizione delle scelte'),
                  'is_required': _('Obbligatorio'),
                  'aiuto': _('Aiuto'),
                  'ordinamento': _('Ordinamento')
                  }
        help_texts = {'name': _("Il nome che comparirà nel form"),
                      'pre_text': _("Da visualizzare prima del campo "
                                    "(accetta formattazione Markdown)"),
                      'aiuto': _("Testo per guidare nella fase di compilazione"),
                      'ordinamento': _("Posizione nel form rispetto agli altri campi"),
                      'valore': _("<li>"
                                  "La compilazione di quest'area di testo "
                                  "non avrà effetti sui campi che non "
                                  "accettano una serie di opzioni."
                                  "</li>"
                                  "<li>"
                                  "Se il campo prevede una serie di opzioni "
                                  "(es: <b>Lista di Opzioni, Checkbox multi-valore</b>) "
                                  "queste devono essere definite rispettando la sintassi: "
                                  "<br>"
                                  "\"<b>opzione 1;opzione 2;opzione 3</b>\" "
                                  "(utilizzando, cioè, il '<b>;</b>' come separatore)."
                                  "</li>"
                                  "<li>"
                                  "Per il Checkbox multi-valore, "
                                  "che ammette più di una scelta, "
                                  "è possibile definire anche il numero "
                                  "massimo delle opzioni selezionabili "
                                  "aggiungendo \"#_valore\" in coda "
                                  "<br>"
                                  "(Utilizzando la stringa "
                                  "\"<b>opzione 1;opzione 2;opzione 3#2</b>\", "
                                  "ad esempio, saranno ammesse al massimo 2 scelte)."
                                  "</li>"
                                  "<li>"
                                  "Per gli Inserimenti Multipli (<b>Formset</b>) la sintassi "
                                  "prevede la definizione di ogni singolo campo "
                                  "che andrà a comporre la tabella:"
                                  "<br>"
                                  "<b>denominazione_campo1({'type':'classe tipo campo', 'choices': 'eventuali opzioni',})#denominazione_campo_2</b>..."
                                  "<br>"
                                  "Con il '<b>#</b>' si separano i singoli campi. "
                                  "Se il tipo non è specificato, di default viene creato un campo di testo."
                                  "<br>"
                                  "(Utilizzando la stringa \"<b>campo1({'type':'CustomSelectBoxField', 'choices': 'scelta1;scelta2;scelta3',})#campo2#campo3({'type':'BaseDateField'})</b>\", "
                                  "ad esempio, verrà creata una tabella con i seguenti campi: "
                                  "una SelectBox con 3 opzioni, un campo di Testo semplice e un campo di tipo data)."
                                  "<br>"
                                  "Le definizioni delle classi dei campi sono disponibili <a href='https://github.com/UniversitaDellaCalabria/django-form-builder/blob/master/django_form_builder/dynamic_fields.py'>qui</a>."
                                  "</li>"
                                  )
                     }
        widgets = {'field_type': BootstrapItaliaSelectWidget,
                   'valore': forms.Textarea(attrs={'rows':2}),
                   'pre_text': forms.Textarea(attrs={'rows':2})}

    class Media:
        js = ('js/textarea-autosize.js',)


class TaskCloseForm(forms.Form):
    status = forms.TypedChoiceField(choices=settings.CLOSING_LEVELS,
                                    required=True,
                                    initial=1,
                                    label=_('Stato chiusura'),
                                    coerce=int,
                                    widget=BootstrapItaliaSelectWidget)
    note = forms.CharField(label=_('Motivazione'),
                           widget=forms.Textarea(attrs={'rows':2}),
                           required=True)

    class Media:
        js = ('js/textarea-autosize.js',)


class BaseTicketCloseForm(forms.Form):
    note = forms.CharField(label=_('Motivazione'),
                           help_text=_('Inserisci il tag {user} per inserire '
                                       'automaticamente il nome e cognome '
                                       'dell\'utente che ha creato la richiesta'),
                           widget=forms.Textarea(attrs={'rows':2}),
                           required=True)

    class Media:
        js = ('js/textarea-autosize.js',)


class TicketCloseForm(BaseTicketCloseForm):
    status = forms.TypedChoiceField(choices=settings.CLOSING_LEVELS,
                                    required=True,
                                    initial=1,
                                    label=_('Stato chiusura'),
                                    coerce=int,
                                    widget=BootstrapItaliaSelectWidget)

    field_order = ['status', 'note']


class OfficeForm(ModelForm):
    """
    """
    class Meta:
        model = OrganizationalStructureOffice
        fields = ['name', 'description', 'is_private']
        labels = {'name': _('Nome'),
                  'description': _('Descrizione'),
                  'is_private': _('Ad uso interno')}
        help_texts = {'is_private': _("Visibile esclusivamente all'interno "
                                      "della struttura quando si effettua "
                                      "un trasferimento di competenza")}
        widgets = {'description': forms.Textarea(attrs={'rows':2})}

    class Media:
        js = ('js/textarea-autosize.js',)


class MyOperatorChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return "{} - {} {}".format(obj.taxpayer_id,
                                   obj.last_name,
                                   obj.first_name)

class OfficeAddOperatorForm(forms.Form):
    operatore = MyOperatorChoiceField(label=_('Assegna operatore'),
                                       queryset=None, required=True,
                                       widget=BootstrapItaliaSelectWidget)
    description = forms.CharField(label=_('Note'),
                                  widget=forms.Textarea(attrs={'rows':2}),
                                  required=False)
    def __init__(self, *args, **kwargs):
        structure = kwargs.pop('structure', None)
        office_slug = kwargs.pop('office_slug', '')
        osoe = OrganizationalStructureOfficeEmployee
        actual = []
        actual_employees = osoe.objects.filter(office__slug=office_slug)
        for ae in actual_employees:
            actual.append(ae.employee.pk)
        employees_list = get_user_model().objects.all().exclude(pk__in=actual)
        super().__init__(*args, **kwargs)
        self.fields['operatore'].queryset = employees_list

    class Media:
        js = ('js/textarea-autosize.js',)


class OrganizationalStructureAddManagerForm(forms.Form):
    manager = MyOperatorChoiceField(label=_('Assegna manager'),
                                    queryset=None, required=True,
                                    widget=BootstrapItaliaSelectWidget)
    def __init__(self, *args, **kwargs):
        structure = kwargs.pop('structure', None)
        manager_users = kwargs.pop('manager_users', None)
        if not manager_users:
            manager_users = structure.get_structure_managers()
        manager_list = []
        for manager_user in manager_users:
            manager_list.append(manager_user.user.pk)
        users_list = get_user_model().objects.all().exclude(pk__in=manager_list)
        super().__init__(*args, **kwargs)
        self.fields['manager'].queryset = users_list

    class Media:
        js = ('js/textarea-autosize.js',)


class PriorityForm(forms.Form):
    priorita = forms.TypedChoiceField(choices=settings.PRIORITY_LEVELS,
                                      required=True,
                                      initial=0,
                                      label=_('Priorità'),
                                      coerce=int,
                                      widget=BootstrapItaliaSelectWidget)


class TakeTicketForm(forms.Form):
    priority = forms.TypedChoiceField(choices=settings.PRIORITY_LEVELS,
                                      required=True,
                                      initial=0,
                                      label=_('Priorità'),
                                      coerce=int,
                                      widget=BootstrapItaliaSelectWidget)
    office = forms.CharField(required=True)

    def __init__(self, *args, **kwargs):
        office_arg = kwargs.pop('office_referred', None)
        super().__init__(*args, **kwargs)
        self.fields['office'].widget=forms.HiddenInput(attrs={'value': office_arg})


class ReplyForm(ModelForm):
    """
    """
    class Meta:
        model = TicketReply
        fields = ['subject', 'text', 'attachment']
        labels = {'subject': _('Oggetto'),
                  'text': _('Testo'),
                  'attachment': _('Allegato')}
        widgets = {'text': forms.Textarea(attrs={'rows':2})}

    class Media:
        js = ('js/textarea-autosize.js',)


class TicketCompetenceForm(forms.Form):
    structures = forms.ModelChoiceField(queryset=None, required=True,
                                        widget=BootstrapItaliaSelectWidget)
    offices = forms.ModelChoiceField(queryset=None, required=True,
                                     widget=BootstrapItaliaSelectWidget)
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
    # category_slug = forms.CharField(label=_('Categoria'), required=True)
    office_slug = forms.CharField(label=_('Ufficio'), required=True)
    follow = forms.BooleanField(label=_('Continua a seguire'), required=False)
    readonly = forms.BooleanField(label=_('Sola lettura'), required=False)
    selected_office = forms.CharField(label=_('Ufficio selezionato'), required=False)


class MyDependenceChoiceField(ModelChoiceField):
    def label_from_instance(self, obj):
        return "{} - {}".format(obj.created_by, obj)

class TicketDependenceForm(forms.Form):
    """
    """
    ticket = MyDependenceChoiceField(queryset=None, required=True,
                                     widget=BootstrapItaliaSelectWidget)
    note = forms.CharField(label=_('Note'),
                           widget=forms.Textarea(attrs={'rows':2}),
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


class TaskForm(ModelForm):
    """
    """
    class Meta:
        model = Task
        fields = ['subject', 'description', 'priority',
                  'is_public', 'attachment']
        labels = {'subject': _('Oggetto'),
                  'description': _('Testo'),
                  'priority': _('Priorità'),
                  'attachment': _('Allegato'),
                  'is_public': _("Visibile all'utente")}
        widgets = {'priority': BootstrapItaliaSelectWidget,
                   'description': forms.Textarea(attrs={'rows':2})}

    class Media:
        js = ('js/textarea-autosize.js',)


class CategoryConditionForm(ModelForm):
    class Meta:
        model = TicketCategoryCondition
        fields = ['title', 'text', 'ordinamento', 'attachment',
                  'is_collapsable', 'is_printable','is_active',]
        labels = {'title': _('Titolo'),
                  'text': _('Testo'),
                  'ordinamento': _('Ordinamento'),
                  'attachment': _('Allegato'),
                  'is_collapsable': _('Collassabile (in nuova richiesta)'),
                  'is_printable': _('Visibile nel documento di stampa'),
                  'is_active': _('Attiva'),}
        widgets = {'text': forms.Textarea(attrs={'rows':2})}

    class Media:
        js = ('js/textarea-autosize.js',)


class CategoryDefaultReplyForm(ModelForm):
    class Meta:
        model = TicketCategoryDefaultReply
        fields = ['text',]
                  # 'is_active',]
        labels = {'text': _('Testo'),}
        help_texts = {'text': _('Inserisci il tag {user} per inserire '
                                'automaticamente il nome e cognome '
                                'dell\'utente che ha creato la richiesta')
                     }
                  # 'is_active': _('Attiva'),}
        widgets = {'text': forms.Textarea(attrs={'rows':2})}

    class Media:
        js = ('js/textarea-autosize.js',)


class OfficeAddCategoryForm(forms.Form):
    category = forms.ModelChoiceField(label=_('Assegna tipologia di richiesta'),
                                      queryset=None, required=True,
                                      widget=BootstrapItaliaSelectWidget)
    def __init__(self, *args, **kwargs):
        structure = kwargs.pop('structure', None)
        office = kwargs.pop('office', None)
        categories = TicketCategory.objects.filter(organizational_structure=structure).exclude(organizational_office__isnull=False)
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = categories
        self.fields['category'].to_field_name='slug'


# class CategoryTaskForm(TaskForm):
    # is_active = forms.BooleanField(label=_('Attiva'), required=False)
class CategoryTaskForm(ModelForm):
    """
    """
    class Meta:
        model = TicketCategoryTask
        fields = ['subject', 'description', 'priority',
                  'attachment', 'is_public', 'is_active']
        labels = {'subject': _('Oggetto'),
                  'description': _('Testo'),
                  'priority': _('Priorità'),
                  'attachment': _('Allegato'),
                  'is_active': _('Attiva'),
                  'is_public': _("Visibile all'utente")}
        widgets = {'priority': BootstrapItaliaSelectWidget,
                   'description': forms.Textarea(attrs={'rows':2})}

    class Media:
        js = ('js/textarea-autosize.js',)


class AssignTicketToOperatorForm(forms.Form):
    priorita = forms.TypedChoiceField(choices=settings.PRIORITY_LEVELS,
                                      required=True,
                                      initial=0,
                                      label=_('Priorità'),
                                      coerce=int,
                                      widget=BootstrapItaliaSelectWidget)
    assign_to = forms.ModelChoiceField(label=_('Seleziona operatore'),
                                       queryset=None, required=True,
                                       widget=BootstrapItaliaSelectWidget)

    def __init__(self, *args, **kwargs):
        structure = kwargs.pop('structure', None)
        office = kwargs.pop('office', None)
        current_user = kwargs.pop('current_user', None)
        office_employees = OrganizationalStructureOfficeEmployee.objects.filter(office=office,
                                                                                employee__is_active=True).exclude(employee=current_user)
        operators_ids = []
        for oe in office_employees:
            key = oe.employee.pk
            if key not in operators_ids:
                operators_ids.append(key)
        operators = get_user_model().objects.filter(pk__in=operators_ids)
        super().__init__(*args, **kwargs)
        self.fields['assign_to'].queryset = operators


class TicketOperatorOfficesForm(forms.Form):
    office = forms.ModelChoiceField(label=_('Seleziona l\'ufficio'),
                                    queryset=None, required=True,
                                    widget=BootstrapItaliaSelectWidget)
    def __init__(self, *args, **kwargs):
        structure = kwargs.pop('structure', None)
        operator = kwargs.pop('operator', None)
        ticket = kwargs.pop('ticket', None)
        offices_list = []
        assignments = TicketAssignment.objects.filter(ticket=ticket,
                                                      office__organizational_structure=structure,
                                                      office__is_active=True,
                                                      follow=True,
                                                      taken_date__isnull=False)
        for assignment in assignments:
            if user_manage_office(user=operator,
                                  office=assignment.office):
                offices_list.append(assignment.office.pk)

        offices = OrganizationalStructureOffice.objects.filter(pk__in=offices_list)
        super().__init__(*args, **kwargs)
        self.fields['office'].queryset = offices
        self.fields['office'].to_field_name = 'slug'


class OrganizationalStructureWSArchiProModelForm(ModelForm):
    """
    """
    class Meta:
        model = OrganizationalStructureWSArchiPro
        fields = ['name',
                  'protocollo_username',
                  # 'protocollo_password',
                  'protocollo_aoo',
                  'protocollo_agd',
                  'protocollo_uo',
                  'protocollo_email',]
                  # 'protocollo_id_uo',
                  # 'protocollo_cod_titolario',
                  # 'protocollo_fascicolo_numero',
                  # 'protocollo_fascicolo_anno',
                  # 'protocollo_template']
        # help_texts = {'protocollo_email': _('Se vuoto: {}').format(settings.PROT_EMAIL_DEFAULT)}
        # labels = {'protocollo_cod_titolario': _('Codice titolario')}
        widgets = {'name': forms.TextInput(attrs={'disabled': True}),
                   'protocollo_username': forms.TextInput(attrs={'disabled': True}),
                   'protocollo_password': forms.TextInput(attrs={'disabled': True}),
                   'protocollo_aoo': forms.TextInput(attrs={'disabled': True}),
                   'protocollo_agd': forms.TextInput(attrs={'disabled': True}),
                   'protocollo_uo': forms.TextInput(attrs={'disabled': True}),
                   'protocollo_email': forms.TextInput(attrs={'disabled': True}),}
                   # 'protocollo_template': forms.Textarea(attrs={'disabled': True})}

    class Media:
        js = ('js/textarea-autosize.js',)


class CategoryWSArchiProModelForm(forms.ModelForm):

    class Meta:
        model = TicketCategoryWSArchiPro
        fields = ('name',
                  'protocollo_cod_titolario',
                  'protocollo_fascicolo_numero',
                  'protocollo_fascicolo_anno',)
        labels = {'name': _('Denominazione configurazione'),
                  'protocollo_cod_titolario': _('Titolario'),
                  'protocollo_fascicolo_numero': _('Numero Fascicolo'),
                  'protocollo_fascicolo_anno': _('Anno Fascicolo')}
        help_texts = {'name': _('A discrezione dell\'utente. Es: "Configurazione anno 2020"'),}
        widgets = {'protocollo_cod_titolario': BootstrapItaliaSelectWidget}

    class Media:
        js = ('js/textarea-autosize.js',)


class OrganizationalStructureAlertForm(ModelForm):
    class Meta:
        model = OrganizationalStructureAlert
        fields = ['name', 'text',
                  'ordinamento',
                  'date_start',
                  'date_end',
                  'is_active']
        labels = {'name': _('Nome'),
                  'text': _('Testo'),
                  'is_active': _('Attiva'),
                  }
        widgets = {'text': forms.Textarea(attrs={'rows':2}),
                   'date_start': UniTicketDateTimeWidget,
                   'date_end': UniTicketDateTimeWidget}
        help_texts = {'date_start': _("Formato {}. Lasciare vuoto  per non impostare"
                                      "").format(settings.DEFAULT_DATETIME_FORMAT.replace('%','')),
                      'date_end': _("Formato {}. Lasciare vuoto  per non impostare"
                                    "").format(settings.DEFAULT_DATETIME_FORMAT.replace('%',''))}

    class Media:
        js = ('js/textarea-autosize.js',)
