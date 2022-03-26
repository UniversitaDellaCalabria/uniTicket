import json
import os
import re

from collections import OrderedDict
from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.templatetags.static import static
from django.core.validators import RegexValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from django_form_builder.dynamic_fields import format_field_name, get_fields_types
from django.conf import settings
from django_form_builder.forms import BaseDynamicForm
from django_form_builder.models import DynamicFieldMap, SavedFormContent
from django_form_builder.utils import get_as_dict, set_as_dict
from organizational_area.models import (OrganizationalStructure,
                                        OrganizationalStructureOffice,
                                        OrganizationalStructureOfficeEmployee,)
from uni_ticket.settings import CLOSING_LEVELS, NEW_TICKET_CREATED_ALERT, ORGANIZATION_EMPLOYEE_LABEL, ORGANIZATION_USER_LABEL, PRIORITY_LEVELS, SHOW_HEADING_TEXT

from . dynamic_form import DynamicForm
from . utils import *
from . validators import *


def _attachment_upload(instance, filename):
    """
    this function has to return the location to upload the file
    """
    folder = instance.get_folder()
    return os.path.join('{}/{}'.format(folder, filename))


class ExpirableModel(models.Model):
    date_start = models.DateTimeField(_("Attiva dal"), null=True, blank=True)
    date_end = models.DateTimeField(_("Attiva fino al"), null=True, blank=True)

    class Meta:
        abstract = True

    def is_expired(self):
        if not self.date_end: return False
        return timezone.localtime() >= self.date_end

    def is_started(self):
        if not self.date_start: return True
        return timezone.localtime() >= self.date_start

    def is_in_progress(self):
        return self.is_started() and not self.is_expired()

    def is_published(self):
        return self.is_active and self.is_in_progress()

    def disable_if_expired(self):
        if self.is_active and self.is_expired():
            self.is_active = False
            self.save(update_fields=['is_active'])


class TimeStampedModel(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    modified =  models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class TicketCategory(ExpirableModel, TimeStampedModel):
    """
    Categoria di appartenenza dei Ticket
    Definisce un particolare ambito
    """
    name = models.CharField(max_length=255,
                            validators=[
                                RegexValidator(
                                    regex='^(?=.*[a-zA-Z])',
                                    message=_("Il nome deve contenere almeno un carattere alfabetico"),
                                    code='invalid_name'
                                ),
                            ])
    slug = models.SlugField(max_length=255,
                            blank=False, null=False)
    description = models.TextField(max_length=500, null=True, blank=True)
    organizational_structure = models.ForeignKey(OrganizationalStructure,
                                                 on_delete=models.PROTECT)
    organizational_office = models.ForeignKey(OrganizationalStructureOffice,
                                              on_delete=models.SET_NULL,
                                              null=True, blank=True)
    is_active = models.BooleanField(default=False,
                                    help_text=_("Se disabilitato, non sarà "
                                                "visibile in Aggiungi Richiesta"))
    not_available_message = models.CharField(_("Messaggio se non attiva"),
                                             max_length=255,
                                             null=True, blank=True,
                                             help_text=_("Viene mostrato agli utenti "
                                                         "se cercano di accedere al form"))
    show_heading_text = models.BooleanField(_("Mostra agli utenti un testo "
                                              "di accettazione in fase di "
                                              "apertura nuova richiesta"),
                                            default=SHOW_HEADING_TEXT)
    # fields to map roles
    allow_anonymous = models.BooleanField(_("Accessibile a Utenti anonimi"),
                                          default=False)
    allow_guest = models.BooleanField(_("Accessibile a Ospiti"), default=True)
    allow_user = models.BooleanField(_("Accessibile a {}").format(ORGANIZATION_USER_LABEL), default=True)
    allow_employee = models.BooleanField(_("Accessibile a {}").format(ORGANIZATION_EMPLOYEE_LABEL), default=True)

    # allowed users
    allowed_users = models.ManyToManyField(settings.AUTH_USER_MODEL,
                                           blank=True)

    # ticket type = notification
    is_notification = models.BooleanField(_("Richiesta di tipo Notifica"),
                                            default=False,
                                            help_text=_("Richiesta che viene "
                                                        "automaticamente presa "
                                                        "in carico"))
    confirm_message_text = models.TextField(_("Messaggio di conferma"),
                                            max_length=500,
                                            blank=True,
                                            null=True,
                                            help_text=_("Es: 'Hai correttamente "
                                                        "confermato la tua partecipazione'. "
                                                        "Apri e chiudi le parentesi graffe "
                                                        "per inserire l'oggetto della richiesta. "
                                                        "Lascia vuoto per usare il testo predefinito \"{}\""
                                                        "").format(NEW_TICKET_CREATED_ALERT))
    footer_text = models.TextField(_("Testo in calce per versione stampabile"),
                                     blank=True,
                                     null=True)
    # fields to map roles
    receive_email = models.BooleanField(_("Mail ad operatori"),
                                        default=False,
                                        help_text=_("Invia email a operatori per ogni richiesta aperta"))

    # protocol action required
    protocol_required = models.BooleanField(_("Protocollo obbligatorio"),
                                            default=False)

    # user can open multiple ticket of this category
    user_multiple_open_tickets = models.BooleanField(
        _("Gli utenti possono aprire più richieste contemporaneamente"),
        default=True
    )

    class Meta:
        unique_together = ("slug", "organizational_structure")
        ordering = ["name"]
        verbose_name = _("Categoria della Richiesta")
        verbose_name_plural = _("Categorie delle Richieste")

    def can_be_deleted(self):
        """
        Ritorna True se è possibile eliminare la categoria
        """
        moduli = TicketCategoryModule.objects.filter(ticket_category=self)
        for modulo in moduli:
            if not modulo.can_be_deleted():
                return False
        return True

    def something_stops_activation(self):
        category_module = TicketCategoryModule.objects.filter(
            ticket_category=self,
            is_active=True
        )
        if not self.organizational_office:
            return _("Per attivare la tipologia di richiesta <b>{}</b> è necessario"
                    " assegnare un ufficio di competenza").format(self)
        elif not self.organizational_office.is_active:
            return _("Per attivare la tipologia di richiesta <b>{}</b> è necessario"
                     " attivare l'ufficio <b>{}</b>").format(self,
                                                             self.organizational_office)
        elif not category_module:
            return _("Per attivare la tipologia di richiesta <b>{}</b> è necessario"
                     " attivare un modulo di input").format(self)
        # elif not self.is_started():
            # return _("Per attivare la tipologia di richiesta <b>{}</b> è necessario"
                     # " rimuovere o attendere la data di inizio").format(self)
        elif self.is_expired():
            return _("Per attivare la tipologia di richiesta <b>{}</b> è necessario"
                     " rimuovere o prolungare la data di scadenza").format(self)
        return False

    def get_folder(self):
        """
        Returns ticket attachments folder path
        """
        folder = '{}/{}/{}/{}'.format(settings.STRUCTURES_FOLDER,
                                      self.organizational_structure.slug,
                                      settings.TICKET_CATEGORIES_FOLDER,
                                      self.slug)
        return folder

    def get_conditions(self, is_printable=False):
        """
        """
        conditions = TicketCategoryCondition.objects.filter(category=self,
                                                            is_active=True)
        if is_printable:
            conditions = conditions.filter(is_printable=True)
        return conditions

    def get_tasks(self, is_active=True):
        tasks = TicketCategoryTask.objects.filter(category=self)
        if is_active:
            tasks = tasks.filter(is_active=True)
        return tasks

    def allowed_to_user(self, user):
        if not user: return False
        if self.allow_anonymous: return True
        if self.allow_guest: return True

        is_employee = user_is_employee(user)
        if is_employee and self.allow_employee:
            return True
        if user_is_in_organization(user) and self.allow_user: return True
        return False

    def get_active_protocol_configuration(self):
        # if structure hasn't an active configuration returns False
        oswap = OrganizationalStructureWSProtocollo
        str_conf = oswap.get_active_protocol_configuration(self.organizational_structure)
        if not str_conf: return False

        # returns category active configuration or False
        tcwap = TicketCategoryWSProtocollo
        conf = tcwap.objects.filter(ticket_category=self,
                                    is_active=True).first()

        return conf if conf else False

    def __str__(self):
        return '{}'.format(self.name)


class TicketCategoryModule(models.Model):
    """
    Modulo di input per i ticket di una categoria
    """
    name = models.CharField(max_length=255)
    ticket_category = models.ForeignKey(TicketCategory,
                                        on_delete = models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created"]
        verbose_name = _("Modulo di Inserimento Richiesta")
        verbose_name_plural = _("Moduli di Inserimento Richieste")

    def can_be_deleted(self):
        """
        """
        # if self.is_active: return False
        ticket_collegati = Ticket.objects.filter(input_module=self).first()
        if ticket_collegati: return False
        return True

    def disable_other_modules(self):
        others = TicketCategoryModule.objects.filter(ticket_category=self.ticket_category).exclude(pk=self.pk)
        for other in others:
            other.is_active = False
            other.save(update_fields = ['is_active'])

    def get_form(self,
                 data=None,
                 files=None,
                 remove_filefields=False,
                 remove_datafields=False,
                 show_conditions=False,
                 **kwargs):
        ticket_input_list = self.ticketcategoryinputlist_set.all().order_by('ordinamento')

        # Static method of BaseDynamicForm
        constructor_dict = BaseDynamicForm.build_constructor_dict(ticket_input_list)

        custom_params = {}
        custom_params['show_conditions'] = show_conditions
        custom_params['category_owner'] = self.ticket_category
        custom_params['subject_initial'] = self.ticket_category.name
        custom_params['description_initial'] = self.ticket_category.description
        custom_params['current_user'] = kwargs.get('current_user')
        custom_params['lang'] = settings.LANGUAGE_CODE

        # get_form(): class method of BaseDynamicForm
        form = BaseDynamicForm.get_form(class_obj=DynamicForm,
                                        constructor_dict=constructor_dict,
                                        custom_params=custom_params,
                                        data=data,
                                        files=files,
                                        remove_filefields=remove_filefields,
                                        remove_datafields=remove_datafields)

        return form

    def __str__(self):
        return '{}'.format(self.name)


# Solo gli utenti Amministratori (lato frontend) possono
# definire i Form di inserimento per ogni categoria di ticket
class TicketCategoryInputList(DynamicFieldMap):
    """
    Classe per la generazione dinamica di forms di inserimento ticket
    """
    category_module = models.ForeignKey(TicketCategoryModule,
                                        on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('Modulo di inserimento')
        verbose_name_plural = _('Moduli di inserimento')
        ordering = ['ordinamento']

    @staticmethod
    def field_exist(module, field_name):
        field = TicketCategoryInputList.objects.filter(category_module=module,
                                                       name__iexact=field_name).first()
        if field: return field_name
        return False


class Ticket(SavedFormContent):
    """
    Ticket
    """
    code = models.CharField(max_length=255, unique=True, db_index=True)
    subject = models.CharField(max_length=255)
    description = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.SET_NULL,
                                   null=True,
                                   related_name='created_by_user')
    compiled = models.DateTimeField(null=True, blank=True)
    compiled_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                    on_delete=models.SET_NULL,
                                    null=True,
                                    blank=True,
                                    related_name='compiled_by_user')
    input_module = models.ForeignKey(TicketCategoryModule,
                                     on_delete=models.PROTECT)
    is_closed = models.BooleanField(default=False)
    closed_date = models.DateTimeField(blank=True, null=True)
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  on_delete=models.SET_NULL,
                                  null=True, blank=True,
                                  related_name='closed_by_user')
    closing_reason = models.TextField(blank=True, null=True)
    closing_status = models.IntegerField(choices=CLOSING_LEVELS,
                                         null=True,
                                         blank=True)
    priority = models.IntegerField(choices=PRIORITY_LEVELS,
                                   default=0)

    # ticket type = notification
    is_notification = models.BooleanField(_("Richiesta di tipo Notifica"),
                                          default=False)

    # protocol
    protocol_number = models.CharField(blank=True, default='',
                                       max_length=32)
    protocol_date = models.DateTimeField(help_text=_("Quando la richiesta è stato protocollata"),
                                         blank=True, null=True)

    class Meta:
        ordering = ["is_closed",
                    "priority",
                    # "is_taken",
                    "-created",
                    "code"]
        verbose_name = _("Ticket")
        verbose_name_plural = _("Ticket")

    def get_category(self):
        return self.input_module.ticket_category

    def get_folder(self):
        """
        Returns ticket attachments folder path
        """
        folder = '{}/{}/{}'.format(settings.TICKET_ATTACHMENT_FOLDER,
                                   self.get_year(),
                                   self.code)
        return folder

    def compress_modulo_compilato(self, check_length=True):
        # if check on length is abled and length is short
        if check_length and not len(self.modulo_compilato) > settings.TICKET_MIN_DIGITS_TO_COMPRESS:
            return
        self.modulo_compilato = compress_text_to_b64(self.modulo_compilato).decode()
        self.save(update_fields=['modulo_compilato'])

    def get_modulo_compilato(self):
        try:
            json_dict = json.loads(decompress_text(self.modulo_compilato))
        except:
            json_dict = json.loads(self.modulo_compilato)
        return json_dict

    @staticmethod
    def get_user_ticket_per_day(user, date=None):
        """
        """
        dt = date if date else timezone.now().date()
        tickets = Ticket.objects.filter(created_by=user,
                                        created__contains=dt)
        return tickets

    def get_url(self, structure=None):
        """
        if structure is present means that the requested url is for
        management
        """
        if structure:
            return reverse('uni_ticket:manage_ticket_url_detail', kwargs={'ticket_id': self.code,
                                                                          'structure_slug': structure.slug})

        return reverse('uni_ticket:ticket_detail', kwargs={'ticket_id': self.code})

    @staticmethod
    def number_limit_reached_by_user(user):
        """
        """
        if settings.MAX_DAILY_TICKET_PER_USER == 0: return False
        today_tickets = Ticket.get_user_ticket_per_day(user=user).count()
        if today_tickets < settings.MAX_DAILY_TICKET_PER_USER: return False
        return True

    @staticmethod
    def existent_open_ticket(user, ticket_category):
        """
        """
        open_tickets = Ticket.objects.filter(created_by=user,
                                             input_module__ticket_category=ticket_category,
                                             is_closed=False)
        return True if open_tickets else False

    def get_year(self):
        """
        """
        return self.created.year

    def is_open(self, user=None):
        if self.is_closed: return False
        if not self.has_been_taken(user=user): return False
        return True

    def check_if_owner(self, user):
        """
        Ritorna True se l'utente passato come argomento ha creato il ticket
        """
        if not user: return False
        if user == self.created_by or user == self.compiled_by: return True

    def get_owners_html(self):
        if self.compiled_by:
            return '<span style="white-space:nowrap">' \
                   '- {} </span>' \
                   '<br>' \
                   '<span style="white-space:nowrap">' \
                   '- {}</span>'.format(self.created_by, self.compiled_by)
        return self.created_by

    def get_owners(self):
        owners = [self.created_by]
        if self.compiled_by: owners.append(self.compiled_by)
        return owners

    def get_allegati_dict(self, ticket_dict={}):
        allegati_dict = {}
        if ticket_dict:
            allegati_dict = ticket_dict.get(settings.ATTACHMENTS_DICT_PREFIX)
        else:
            # json_dict = json.loads(self.get_modulo_compilato())
            json_dict = self.get_modulo_compilato()
            allegati_dict = get_as_dict(compiled_module_json=json_dict).get(settings.ATTACHMENTS_DICT_PREFIX)
        return allegati_dict or {}

    def get_form_module(self):
        """
        Ritorna il modulo di input con cui il ticket è stato compilato
        """
        return self.input_module

    def compiled_form(self, files=None,
                      remove_filefields=True,
                      remove_datafields=False):
        """
        Torna il form compilato senza allegati
        """
        modulo = self.get_form_module()
        if not modulo: return None
        extra_datas = {}
        extra_datas[settings.TICKET_SUBJECT_ID] = self.subject
        extra_datas[settings.TICKET_DESCRIPTION_ID] = self.description
        form = SavedFormContent.compiled_form(data_source=json.dumps(self.get_modulo_compilato()),
                                              extra_datas=extra_datas,
                                              files=files,
                                              remove_filefields=remove_filefields,
                                              remove_datafields=remove_datafields,
                                              form_source=modulo)
        return form

    def save_data(self, subject, description, ticket_dict):
        self.subject = subject
        self.description = description
        set_as_dict(self, ticket_dict,
                    fields_to_pop=[settings.TICKET_SUBJECT_ID,
                                   settings.TICKET_DESCRIPTION_ID])

    # HTML representation of status
    def get_status(self):
        if self.is_closed:
            # if is a notification ticket
            if self.is_notification or not self.closed_by:
                return _('<span class="badge badge-success">Chiusa</span>')
            # normal ticket
            status_literal = dict(CLOSING_LEVELS).get(self.closing_status)
            html = _('<span class="badge badge-success">Chiusa</span> '
                      '<span class="badge badge-{}">{}</span>')
            if self.closing_status == -1:
                html = html.format("danger", status_literal)
            elif self.closing_status == 0:
                html = html.format("warning", status_literal)
            elif self.closing_status == 1:
                html = html.format("success", status_literal)
            elif self.closing_status == 2:
                html = html.format("secondary", status_literal)
            return '{}<br><small>{}</small>'.format(html, self.closed_by)
        if not self.has_been_taken():
            return _('<span class="badge badge-danger">Aperta</span>')
        return _('<span class="badge badge-warning">Assegnata</span> {}'
                 '').format(self.taken_by_html_list())

    # for datatables (show icons)
    def get_status_table(self):
        if self.is_closed:
            # if is a notification ticket
            if self.is_notification or not self.closed_by:
                return _('<span class="badge badge-success">Chiusa</span>')
            # normal ticket
            status_literal = dict(CLOSING_LEVELS).get(self.closing_status)

            # get svg file from static
            static_icon = static('svg/sprite.svg')

            html = _('<span class="badge badge-success">Chiusa</span> '
                      '<svg class="icon icon-xs {}">'
                      '<title>{}</title>'
                      '<use xlink:href="{}#{}"></use>'
                      '</svg>')

            if self.closing_status == -1:
                html = html.format("icon-danger", status_literal,
                                   static_icon, "it-close-circle")
            elif self.closing_status == 0:
                html = html.format("icon-warning", status_literal,
                                   static_icon, "it-warning-circle")
            elif self.closing_status == 1:
                html = html.format("icon-success", status_literal,
                                   static_icon, "it-check-circle")
            elif self.closing_status == 2:
                html = html.format("icon-secondary", status_literal,
                                   static_icon, "it-minus-circle")
            return '{}<br><small>{}</small>'.format(html, self.closed_by)
        if not self.has_been_taken():
            return _('<span class="badge badge-danger">Aperta</span>')
        return _('<span class="badge badge-warning">Assegnata</span> {}'
                 '').format(self.taken_by_html_list())

    def update_log(self, user, note='', send_mail=True, mail_msg=''):
        if not user: return False
        if send_mail:
            # Send mail to ticket owner
            d = {'hostname': settings.HOSTNAME,
                 'user': self.created_by,
                 'message': mail_msg or note,
                 'ticket': self
                }
            m_subject = _('{} - richiesta {} aggiornata'.format(settings.HOSTNAME,
                                                             self))
            # Start send mail to ticket owner
            send_custom_mail(subject=m_subject,
                             recipients=self.get_owners(),
                             body=settings.TICKET_UPDATED,
                             params=d)
            # End send mail to ticket owner

        LogEntry.objects.log_action(user_id         = user.pk,
                                    content_type_id = ContentType.objects.get_for_model(self).pk,
                                    object_id       = self.pk,
                                    object_repr     = self.__str__(),
                                    action_flag     = CHANGE,
                                    change_message  = note)

    def get_assigned_to_offices(self,
                                office_active=True,
                                structure=None,
                                ignore_follow=True):
        """
        Returns to wicth offices ticket is assigned
        """
        assignments = TicketAssignment.objects.filter(ticket=self)
        if not ignore_follow:
            assignments = assignments.filter(follow=True)
        offices = []
        for assignment in assignments:
            office = assignment.office
            if structure and not office.organizational_structure==structure:
                continue
            if not office_active: offices.append(office)
            elif office.is_active: offices.append(office)
        return offices

    def get_assigned_to_structures(self, ignore_follow=True):
        """
        Returns to wich structures ticket is assigned
        """
        offices = self.get_assigned_to_offices(office_active=False,
                                               ignore_follow=ignore_follow)
        structures = []
        for office in offices:
            struct = office.organizational_structure
            if struct not in structures:
                structures.append(struct)
        return structures

    def add_competence(self, office, user, note=None):
        """
        Aggiunge un nuovo ufficio di competenza per la gestione
        del ticket
        """
        competence = TicketAssignment.objects.filter(ticket=self,
                                                     office=office).first()
        if competence: return False
        new_competence = TicketAssignment(ticket=self,
                                          office=office,
                                          note=note,
                                          assigned_by=user)

        # if user that transfer competence is a destination office operator
        # he takes competence in destination office
        if OrganizationalStructureOfficeEmployee.objects.filter(employee=user, office=office):
            new_competence.taken_by = user
            new_competence.taken_date = timezone.localtime()

        new_competence.save()
        return new_competence

    def block_competence(self,
                         user,
                         structure,
                         allow_readonly=True,
                         selected_office=None):
        """
        """
        usertype = get_user_type(user, structure)
        if usertype == 'user': return False

        offices_to_disable = []

        if selected_office and user_manage_office(user, selected_office):
            if not selected_office.is_default:
                competence = TicketAssignment.objects.filter(ticket=self,
                                                             office=selected_office,
                                                             taken_date__isnull=False).first()
                competence.follow = allow_readonly
                competence.readonly = allow_readonly
                competence.save(update_fields = ['follow',
                                                 'readonly'])
            offices_to_disable.append(selected_office)
        else:
            offices = self.get_assigned_to_offices(office_active=False,
                                                   structure=structure)

            if usertype == 'operator':
                for office in offices:
                    # default office can't be unassigned
                    if office.is_default: continue
                    office_employee = OrganizationalStructureOfficeEmployee.objects.filter(employee=user,
                                                                                           office=office)
                    if office_employee:
                        offices_to_disable.append(office)
            elif usertype == 'manager': offices_to_disable = offices
            for off in offices_to_disable:
                # default office can't be unassigned
                if off.is_default and allow_readonly: continue
                competence = TicketAssignment.objects.filter(ticket=self,
                                                             office=off,
                                                             taken_date__isnull=False).first()
                if not competence or not competence.follow: continue
                competence.follow = allow_readonly
                competence.readonly = allow_readonly
                competence.save(update_fields = ['follow',
                                                 'readonly'])
        return offices_to_disable

    def get_dependences(self):
        """
        """
        t2t_list = Ticket2Ticket.objects.filter(subordinate_ticket=self).all()
        return t2t_list

    def get_task(self):
        """
        """
        task = []
        ticket_task = Task.objects.filter(ticket=self).all()
        for t in ticket_task:
            task.append(t)
        return task

    def blocks_some_ticket(self):
        """
        """
        dependences = []
        t2t_list = Ticket2Ticket.objects.filter(main_ticket=self).all()
        for t2t in t2t_list:
            dependences.append(t2t.subordinate_ticket)
        return dependences

    def is_closable(self):
        """
        """
        if not self.has_been_taken(): return False
        if self.is_closed: return False
        dependences = self.get_dependences()
        task_list = self.get_task()
        if not dependences and not task_list: return True
        for dependence in dependences:
            if not dependence.main_ticket.is_closed: return False
        for task in task_list:
            if not task.is_closed: return False
        return True

    def is_valid(self):
        """
        """
        json_dict = self.get_modulo_compilato()
        ticket_dict = get_as_dict(json_dict)
        if not settings.ATTACHMENTS_DICT_PREFIX in ticket_dict: return True
        allegati = ticket_dict.get(settings.ATTACHMENTS_DICT_PREFIX)
        # valido solo i campi File vuoti del form
        # evito di validare tutti gli altri campi, sicuramente corretti
        form = self.compiled_form(files=None,
                                  remove_filefields=allegati,
                                  remove_datafields=True)
        if form.is_valid(): return True
        return False

    def get_priority(self):
        """
        """
        # return dict(settings.PRIORITY_LEVELS).get(str(self.priority))
        return dict(PRIORITY_LEVELS).get(self.priority)

    def get_messages_count(self, by_operator=False):
        all_messages = TicketReply.objects.filter(ticket=self)
        first_created = all_messages.first()
        # If I'm a manager/operator
        unread_messages = all_messages.filter(read_date=None)
        # if I'm a simple user, I want my agents replies
        if by_operator:
            unread_messages = unread_messages.exclude(structure=None)
        else:
            unread_messages = unread_messages.filter(structure=None)
        return (all_messages.count(),
                unread_messages.count(),
                first_created.created if first_created else None)

    def _check_assignment_privileges(self, queryset):
        if not queryset: return False
        if queryset.filter(readonly=False):
            readonly_value = False
        elif queryset.filter(readonly=True):
            readonly_value = True
        d = {'follow': True,
             'readonly': readonly_value}
        return d
        # return json.loads(d)

    def is_followed_in_structure(self, structure, taken=False):
        if not structure: return False
        assignment = TicketAssignment.objects.filter(ticket=self,
                                                     office__organizational_structure=structure,
                                                     office__is_active=True,
                                                     follow=True)
        if taken:
            assignment = assignment.filter(taken_date__isnull=False)
        return self._check_assignment_privileges(assignment)

    def is_followed_by_office(self, office, taken=False):
        if not office: return False
        assignment = TicketAssignment.objects.filter(ticket=self,
                                                     office=office,
                                                     office__is_active=True,
                                                     follow=True)
        if taken:
            assignment = assignment.filter(taken_date__isnull=False)
        return self._check_assignment_privileges(assignment)

    def is_followed_by_one_of_offices(self, offices):
        if not offices: return False
        assignment = TicketAssignment.objects.filter(ticket=self,
                                                     office__in=offices,
                                                     follow=True)
        return self._check_assignment_privileges(assignment)

    def has_been_taken(self,
                       user=None,
                       follow=True,
                       exclude_readonly=False,
                       structure=None):
        assignments = TicketAssignment.objects.filter(ticket=self,
                                                      taken_date__isnull=False)
        if follow:
            assignments = assignments.filter(follow=True)
            if exclude_readonly:
                assignments = assignments.filter(readonly=False)
        if structure:
            assignments = assignments.filter(office__organizational_structure=structure)
        if user:
            assignments = assignments.filter(taken_by=user)
        return True if assignments else False

    def has_been_taken_by_user(self,
                               user,
                               follow=True,
                               exclude_readonly=False,
                               structure=None):
        if not user: return False
        assignments = TicketAssignment.objects.filter(ticket=self,
                                                      taken_by=user)
        if structure:
            assignments = assignments.filter(office__organizational_structure=structure)
        if follow:
            assignments = assignments.filter(follow=True)
            if exclude_readonly:
                assignments = assignments.filter(readonly=False)
        return True if assignments else False

    def taken_by_html_list(self):
        office_operators = {}
        assignments = TicketAssignment.objects.filter(ticket=self)
        elements = ""
        for assignment in assignments:
            assigned = assignment.taken_by or _("Da assegnare")
            element = "<li><small><b>{}</b></small>: ".format(assignment.office)
            if assignment.taken_by:
                element +=  "<small>{}</small></li>".format(assignment.taken_by)
            else:
                element +=  "<span class=\"badge badge-danger\">{}</span></li>".format(_("Da assegnare"))
            elements += element
        return '<ul>{}</ul>'.format(elements)

    def take(self, user, structure, assigned_by=None, strictly_assigned=False):
        assignments = TicketAssignment.objects.filter(ticket=self,
                                                      office__organizational_structure=structure)
        for assignment in assignments:
            if user_manage_office(user=user,
                                  office=assignment.office,
                                  strictly_assigned=strictly_assigned) and not assignment.taken_date:
                assignment.taken_date = timezone.localtime()
                assignment.taken_by = user
                if assigned_by:
                    assignment.assigned_by = assigned_by
                    assignment.created = timezone.localtime()
                assignment.save()

    def is_untaken_by_user_offices(self, user, structure):
        assignments = TicketAssignment.objects.filter(ticket=self,
                                                      office__organizational_structure=structure)
        offices = []
        for assignment in assignments:
            if user_manage_office(user, assignment.office) and not assignment.taken_date:
                offices.append(assignment.office)
        return offices

    def __str__(self):
        return '{} ({})'.format(self.subject, self.code)


class TicketCategoryDefaultReply(models.Model):
    """
    """
    ticket_category = models.ForeignKey(TicketCategory,
                                        on_delete = models.CASCADE)
    text = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = _("Risposta predefinita")
        verbose_name_plural = _("Risposte predefinite")

    def __str__(self):
        return (self.text[:80] + '..')


class TicketAssignment(TimeStampedModel):
    """
    Ufficio di competenza per la gestione Ticket
    """
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    office = models.ForeignKey(OrganizationalStructureOffice,
                               on_delete=models.PROTECT)
    note = models.TextField(blank=True, null=True)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                    on_delete=models.PROTECT,
                                    null=True)
    taken_date = models.DateTimeField(null=True, blank=True)
    taken_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                 on_delete=models.PROTECT,
                                 null=True, blank=True,
                                 related_name='taken_by_operator')
    follow = models.BooleanField(default=True)
    readonly = models.BooleanField(default=False)

    class Meta:
        unique_together = ("ticket", "office")
        ordering = ["created"]
        verbose_name = _("Competenza Ticket")
        verbose_name_plural = _("Competenza Ticket")

    @staticmethod
    def get_ticket_per_structure(structure, follow_check=True):
        """
        """
        ticket_assignments = TicketAssignment.objects.filter(office__organizational_structure=structure,
                                                             office__is_active=True)\
                                                     .values('ticket__code',
                                                             'follow')
        ticket_set = set()
        for assignment in ticket_assignments:
            if follow_check and not assignment['follow']: continue
            ticket_set.add(assignment['ticket__code'])
        return ticket_set

    @staticmethod
    def get_ticket_in_office_list(office_list, follow_check=True):
        """
        """
        ticket_assignments = TicketAssignment.objects.filter(office__in=office_list,
                                                             office__is_active=True)\
                                                     .values('ticket__code',
                                                             'follow')
        ticket_set = set()
        for assignment in ticket_assignments:
            if follow_check and not assignment['follow']: continue
            ticket_set.add(assignment['ticket__code'])
        return ticket_set

    def __str__(self):
        return '{} - {}'.format(self.ticket, self.office)


class TicketReply(models.Model):
    """
    Cronologia Domande/Riposte utente-agente
    """
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL,
                              on_delete=models.PROTECT)
    structure = models.ForeignKey(OrganizationalStructure,
                                  on_delete=models.SET_NULL,
                                  null=True, blank=True)
    subject = models.CharField(max_length=255)
    text = models.TextField()
    attachment = models.FileField(upload_to=_attachment_upload,
                                  null=True, blank=True,
                                  max_length=255,
                                  validators=[validate_file_extension,
                                              validate_file_size,
                                              validate_file_length])
    created = models.DateTimeField(auto_now_add=True)
    read_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.SET_NULL,
                                null=True, blank=True,
                                related_name='ticket_replies_read_by')
    read_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["ticket", "created"]
        verbose_name = _("Domande/Risposte Ticket")
        verbose_name_plural = _("Domande/Risposte Ticket")

    @staticmethod
    def get_unread_messages_count(tickets, by_operator=False):
        unread_messages = TicketReply.objects.filter(ticket__in=tickets,
                                                     read_date=None)
        # show messages sent by operator
        if by_operator:
           return unread_messages.exclude(structure=None).count()
        # show messages sent by user
        return unread_messages.filter(structure=None).count()

    def get_folder(self):
        """
        Returns ticket attachments folder path
        """
        ticket_folder = self.ticket.get_folder()
        folder = '{}/{}'.format(ticket_folder,
                                settings.TICKET_MESSAGES_ATTACHMENT_SUBFOLDER)
        return folder

    def __str__(self):
        return '{} - {}'.format(self.subject, self.ticket)


class Ticket2Ticket(models.Model):
    """
    Dipendenza Ticket da altri Ticket
    Lo Subordinate non può essere chiuso se ci sono Main da risolvere
    """
    main_ticket = models.ForeignKey(Ticket,
                                    on_delete=models.CASCADE,
                                    related_name="main")
    subordinate_ticket = models.ForeignKey(Ticket,
                                           on_delete=models.CASCADE,
                                           related_name="subordinate")
    note = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("subordinate_ticket", "main_ticket")
        ordering = ["subordinate_ticket", "main_ticket"]
        verbose_name = _("Dipendenza Ticket")
        verbose_name_plural = _("Dipendenze Ticket")

    @staticmethod
    def main_is_already_used(ticket):
        """
        """
        relations = Ticket2Ticket.objects.filter(subordinate_ticket=ticket)
        if not relations: return False
        for relation in relations:
            main = relation.main_ticket
            if not main.is_closed: return True
        return False

    def __str__(self):
        return '{} - {}'.format(self.subordinate_ticket, self.main_ticket)


class AbstractTask(models.Model):
    """
    """
    subject = models.CharField(max_length=255)
    code = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.SET_NULL,
                                   null=True)
    # priority = models.IntegerField(default=0)
    priority = models.IntegerField(choices=PRIORITY_LEVELS,
                                   default=0)
    is_public = models.BooleanField(default=True)
    attachment = models.FileField(upload_to=_attachment_upload,
                                  null=True, blank=True,
                                  max_length=255,
                                  validators=[validate_file_extension,
                                              validate_file_size,
                                              validate_file_length])

    class Meta:
        abstract = True

    def get_priority(self):
        """
        """
        return dict(PRIORITY_LEVELS).get(self.priority)


class Task(AbstractTask):
    """
    ToDo interno alla Struttura che può essere vincolante se associato
    a un Ticket (il Ticket non può essere chiuso se il task non è chiuso)
    """
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    is_closed = models.BooleanField(default=False)
    closed_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                  on_delete=models.SET_NULL,
                                  null=True,
                                  related_name='task_closed_by_user')
    closed_date = models.DateTimeField(blank=True, null=True)
    closing_reason = models.TextField(blank=True, null=True)
    closing_status = models.IntegerField(choices=CLOSING_LEVELS,
                                         null=True,
                                         blank=True)

    class Meta:
        ordering = ["created"]
        verbose_name = _("Task")
        verbose_name_plural = _("Task")

    def update_log(self, user, note=None):
        LogEntry.objects.log_action(user_id         = user.pk,
                                    content_type_id = ContentType.objects.get_for_model(self).pk,
                                    object_id       = self.pk,
                                    object_repr     = self.__str__(),
                                    action_flag     = CHANGE,
                                    change_message  = note)

    def get_folder(self):
        """
        Returns ticket attachments folder path
        """
        ticket_folder = self.ticket.get_folder()
        folder = '{}/{}/{}'.format(ticket_folder,
                                   settings.TICKET_TASK_ATTACHMENT_SUBFOLDER,
                                   self.code)
        return folder

    def get_status(self):
        if self.is_closed:
            status_literal = dict(CLOSING_LEVELS).get(self.closing_status)

            html = _('<span class="badge badge-success">Chiusa</span> '
                      '<span class="badge badge-{}">{}</span>')
            if self.closing_status == -1:
                html = html.format("danger", status_literal)
            elif self.closing_status == 0:
                html = html.format("warning", status_literal)
            elif self.closing_status == 1:
                html = html.format("success", status_literal)
            elif self.closing_status == 2:
                html = html.format("secondary", status_literal)
            return '{} <small>{}</small>'.format(html, self.closed_by)
        return _('<span class="badge badge-danger">Aperta</span>')

    def __str__(self):
        return '{} - ticket: {}'.format(self.subject, self.ticket)


class Task2Ticket(models.Model):
    """
    Dipendenza Ticket da Task
    """
    ticket = models.ForeignKey(Ticket, on_delete=models.PROTECT)
    task = models.ForeignKey(Task, on_delete=models.PROTECT)
    # User o Employee?
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.SET_NULL,
                                   null=True)

    class Meta:
        unique_together = ("ticket", "task")
        ordering = ["task", "ticket"]
        verbose_name = _("Dipendenza Ticket da Task")
        verbose_name_plural = _("Dipendenze Ticket da Task")

    def __str__(self):
        return '{} - {}'.format(self.task, self.ticket)


class TicketCategoryCondition(models.Model):
    """
    """
    category = models.ForeignKey(TicketCategory, on_delete=models.CASCADE)
    title = models.CharField(max_length=255, blank=False, null=False)
    text = models.TextField(blank=False, null=False)
    ordinamento = models.PositiveIntegerField(blank=True, default=0)
    attachment = models.FileField(upload_to=_attachment_upload,
                                  null=True, blank=True,
                                  max_length=255,
                                  validators=[validate_file_extension,
                                              validate_file_size,
                                              validate_file_length])
    is_printable = models.BooleanField(_('Visibile nella versione stampabile'),
                                       default=False)
    is_collapsable = models.BooleanField(_('Collassabile'), default=True)
    is_active = models.BooleanField(_('Visibile agli utenti'), default=True)

    class Meta:
        ordering = ('ordinamento', )
        verbose_name = _('Clausola tipologia di richiesta ticket')
        verbose_name_plural = _('Clausole tipologia di richiesta ticket')

    def get_folder(self):
        """
        Returns ticket attachments folder path
        """
        category_folder = self.category.get_folder()
        return '{}/{}'.format(category_folder,
                              settings.CATEGORY_CONDITIONS_ATTACHMENT_SUBFOLDER)

    def __str__(self):
        return '({}) {}'.format(self.category, self.title)


class TicketCategoryTask(AbstractTask):
    """
    ToDo interno alla Struttura che può essere vincolante se associato
    a un Ticket (il Ticket non può essere chiuso se il task non è chiuso)
    """
    category = models.ForeignKey(TicketCategory, on_delete=models.CASCADE)
    is_active = models.BooleanField(_('Visibile nei ticket'),
                                    default=False)

    class Meta:
        ordering = ["created"]
        verbose_name = _("Task predefinito")
        verbose_name_plural = _("Task predefiniti")

    def get_folder(self):
        """
        Returns ticket attachments folder path
        """
        category_folder = self.category.get_folder()
        folder = '{}/{}/{}'.format(category_folder,
                                   settings.TICKET_TASK_ATTACHMENT_SUBFOLDER,
                                   self.code)
        return folder

    def __str__(self):
        return '{} - {}'.format(self.subject, self.category)


# class AbstractWSProtocollo(models.Model):
    # """
    # """
    # name = models.CharField(max_length=255)
    # created = models.DateTimeField(auto_now_add=True)
    # modified = models.DateTimeField(auto_now=True)
    # is_active = models.BooleanField(default=False)

    # protocollo_aoo = models.CharField('AOO', max_length=12)
    # protocollo_agd = models.CharField('AGD', max_length=12)
    # protocollo_uo = models.CharField('UO', max_length=12,)
    # protocollo_email = models.EmailField('E-mail',
                                         # max_length=255,
                                         # blank=True, null=True)
    # protocollo_id_uo = models.CharField(_('ID Unità Organizzativa'),
                                      # max_length=12)
    # protocollo_cod_titolario = models.CharField(_('Codice titolario'),
                                                # max_length=12,
                                                # choices=settings.TITOLARIO_DICT)
    # protocollo_fascicolo_numero = models.CharField(_('Fascicolo numero'),
                                                   # max_length=12)
                                                   # default=settings.PROTOCOLLO_FASCICOLO_DEFAULT)
    # protocollo_fascicolo_anno = models.IntegerField(_('Fascicolo anno'))
    # protocollo_template = models.TextField('XML template',
                                           # help_text=_('Template XML che '
                                                      # 'descrive il flusso'))

    # class Meta:
        # abstract = True


class OrganizationalStructureWSProtocollo(models.Model):
    organizational_structure = models.ForeignKey(OrganizationalStructure,
                                                 on_delete=models.CASCADE)
    name = models.CharField(_('Denominazione configurazione'),
                            max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)

    protocollo_username = models.CharField('Username', max_length=255)
    protocollo_password = models.CharField('Password', max_length=255)
    protocollo_aoo = models.CharField('AOO', max_length=12)
    protocollo_agd = models.CharField('AGD', max_length=12,
                                      default='', blank=True)

    # protocollo_template = models.TextField('XML template',
                                           # help_text=_('Template XML che '
                                                      # 'descrive il flusso'))

    class Meta:
        ordering = ["-created"]
        verbose_name = _("Configurazione WS Protocollo Struttura")
        verbose_name_plural = _("Configurazioni WS Protocollo Strutture")

    def disable_other_configurations(self):
        others = OrganizationalStructureWSProtocollo.objects.filter(organizational_structure=self.organizational_structure).exclude(pk=self.pk)
        for other in others:
            other.is_active = False
            other.save(update_fields = ['is_active', 'modified'])

    @staticmethod
    def get_active_protocol_configuration(organizational_structure):
        oswsap = OrganizationalStructureWSProtocollo
        conf = oswsap.objects.filter(organizational_structure=organizational_structure,
                                     is_active=True).first()
        return conf if conf else False

    def __str__(self):
        return '{} - {}'.format(self.name, self.organizational_structure)


class TicketCategoryWSProtocollo(TimeStampedModel):
    ticket_category = models.ForeignKey(TicketCategory,
                                        on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    is_active = models.BooleanField(default=False)
    protocollo_uo = models.CharField('UO', max_length=12,
                                     choices=settings.UO_DICT)
    protocollo_uo_rpa = models.CharField('RPA', max_length=255,
                                         default='', blank=True,
                                         help_text=_('Nominativo RPA'))
    protocollo_uo_rpa_username = models.CharField('RPA username', max_length=255,
                                                  default='', blank=True,
                                                  help_text=_('Username RPA sul sistema di protocollo'))
    protocollo_uo_rpa_matricola = models.CharField('RPA matricola', max_length=255,
                                                   default='', blank=True,
                                                   help_text=_('Matricola RPA sul sistema di protocollo'))
    protocollo_send_email = models.BooleanField(_('Invia e-mail a RPA'),
                                                default=True)
    protocollo_email = models.EmailField('E-mail',
                                         max_length=255,
                                         blank=True, null=True,
                                         help_text = 'Se vuoto: {}'.format(settings.PROTOCOL_EMAIL_DEFAULT))
    protocollo_cod_titolario = models.CharField(_('Codice titolario'),
                                                max_length=12,
                                                choices=settings.TITOLARIO_DICT)
    protocollo_fascicolo_numero = models.CharField(_('Fascicolo numero'),
                                                   max_length=255,
                                                   default='', blank=True)
    protocollo_fascicolo_anno = models.IntegerField(_('Fascicolo anno'),
                                                    null=True, blank=True)

    class Meta:
        ordering = ["-created"]
        verbose_name = _("Configurazione WS Protocollo Categoria")
        verbose_name_plural = _("Configurazioni WS Protocollo Categorie")

    def disable_other_configurations(self):
        others = TicketCategoryWSProtocollo.objects.filter(ticket_category=self.ticket_category).exclude(pk=self.pk)
        for other in others:
            other.is_active = False
            other.save(update_fields = ['is_active', 'modified'])

    def __str__(self):
        return '{} - {}'.format(self.name, self.ticket_category)


class OrganizationalStructureAlert(ExpirableModel, TimeStampedModel):
    organizational_structure = models.ForeignKey(OrganizationalStructure,
                                                 on_delete=models.CASCADE)
    name = name = models.CharField(max_length=255)
    text = models.TextField(max_length=500)
    ordinamento = models.PositiveIntegerField(blank=True, default=0)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["ordinamento", "created"]
        verbose_name = _("Alert di struttura agli utenti")

    def __str__(self):
        return '{} - {}'.format(self.name, self.organizational_structure)
