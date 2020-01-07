import json
import os
import re

from collections import OrderedDict
from django.conf import settings
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from django_form_builder.dynamic_fields import format_field_name, get_fields_types
from django_form_builder.models import DynamicFieldMap, SavedFormContent
from django_form_builder.settings import MANAGEMENT_FORMSET_STRINGS
from django_form_builder.utils import get_as_dict, set_as_dict
from organizational_area.models import (OrganizationalStructure,
                                        OrganizationalStructureOffice,
                                        OrganizationalStructureOfficeEmployee,)

from . dynamic_form import DynamicForm
from . settings import *
from . utils import (get_folder_allegato,
                     get_user_type,
                     send_custom_mail,
                     user_is_employee,
                     user_is_in_organization)


def _reply_attachment_upload(instance, filename):
    """
    this function has to return the location to upload the file
    """
    ticket_folder = get_folder_allegato(instance.ticket)
    return os.path.join('{}/{}/{}'.format(ticket_folder,
                                          TICKET_REPLY_ATTACHMENT_SUBFOLDER,
                                          filename))

def _task_attachment_upload(instance, filename):
    """
    this function has to return the location to upload the file
    """
    ticket_folder = get_folder_allegato(instance.ticket)
    return os.path.join('{}/{}/{}/{}'.format(ticket_folder,
                                             TICKET_TASK_ATTACHMENT_SUBFOLDER,
                                             instance.code,
                                             filename))

class TicketCategory(models.Model):
    """
    Categoria di appartenenza dei Ticket
    Definisce un particolare ambito
    """
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=40,
                            blank=False, null=False)
    description = models.TextField(max_length=500, null=True, blank=True)
    created = models.DateTimeField(auto_now=True)
    modified = models.DateTimeField(auto_now=True)
    organizational_structure = models.ForeignKey(OrganizationalStructure,
                                                 on_delete=models.PROTECT)
    organizational_office = models.ForeignKey(OrganizationalStructureOffice,
                                              on_delete=models.SET_NULL,
                                              null=True, blank=True)
    is_active = models.BooleanField(default=False,
                                    help_text=_("Se disabilitato, non sarà "
                                                "visibile in Aggiungi Ticket"))
    # fields to map roles
    allow_guest = models.BooleanField(_("Accessibile agli ospiti"), default=True)
    allow_user = models.BooleanField(_("Accessibile agli utenti dell'organizzazione"), default=True)
    allow_employee = models.BooleanField(_("Accessibile ai dipendenti dell'organizzazione"), default=True)

    def is_eliminabile(self):
        """
        Ritorna True se è possibile eliminare la categoria
        """
        moduli = TicketCategoryModule.objects.filter(ticket_category=self)
        for modulo in moduli:
            if not modulo.is_eliminabile():
                return False
        return True

    def get_conditions(self):
        """
        """
        conditions = TicketCategoryCondition.objects.filter(category=self,
                                                            is_active=True)
        return conditions

    def allowed_to_user(self, user):
        if not user: return False
        if self.allow_guest: return True

        is_employee = user_is_employee(user)
        if is_employee and self.allow_employee:
            return True
        if user_is_in_organization(user) and self.allow_user: return True
        return False

    class Meta:
        unique_together = ("slug", "organizational_structure")
        ordering = ["name"]
        verbose_name = _("Categoria dei Ticket")
        verbose_name_plural = _("Categorie dei Ticket")

    def __str__(self):
        return '{}'.format(self.name)


class TicketCategoryModule(models.Model):
    """
    Modulo di input per i ticket di una categoria
    """
    name = models.CharField(max_length=255)
    ticket_category = models.ForeignKey(TicketCategory,
                                        on_delete = models.CASCADE)
    created = models.DateTimeField(auto_now = True)
    is_active = models.BooleanField(default = False)

    class Meta:
        ordering = ["-created"]
        verbose_name = _("Modulo di Inserimento Ticket")
        verbose_name_plural = _("Moduli di Inserimento Ticket")

    def is_eliminabile(self):
        """
        """
        # if self.is_active: return False
        ticket_collegati = Ticket.objects.filter(input_module=self).first()
        if ticket_collegati: return False
        return True

    def get_form(self,
                 data=None,
                 files=None,
                 remove_filefields=False,
                 remove_datafields=False,
                 show_conditions=False):
        ticket_input_list = self.ticketcategoryinputlist_set.all().order_by('ordinamento')
        # Static method of DynamicFieldMap
        constructor_dict = DynamicFieldMap.build_constructor_dict(ticket_input_list)
        custom_params = {}
        custom_params['show_conditions'] = show_conditions
        custom_params['category_owner'] = self.ticket_category
        form = DynamicFieldMap.get_form(DynamicForm,
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
    code = models.CharField(max_length=255, unique=True)
    subject = models.CharField(max_length=255)
    description = models.TextField()
    created = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.SET_NULL,
                                   null=True)
    input_module = models.ForeignKey(TicketCategoryModule,
                                     on_delete=models.PROTECT)
    is_taken = models.BooleanField(default=False)
    is_closed = models.BooleanField(default=False)
    data_chiusura = models.DateTimeField(blank=True, null=True)
    motivazione_chiusura = models.TextField(blank=True, null=True)
    priority = models.IntegerField(default=0)

    class Meta:
        ordering = ["is_closed",
                    "priority",
                    "is_taken",
                    "-created",
                    "code"]
        verbose_name = _("Ticket")
        verbose_name_plural = _("Ticket")

    def get_category(self):
        return self.input_module.ticket_category

    @staticmethod
    def get_user_ticket_per_day(user, data=None):
        """
        """
        if not data:
            ndata = timezone.datetime(timezone.localdate().year,
                                      timezone.localdate().month,
                                      timezone.localdate().day,
                                      tzinfo=timezone.get_default_timezone())
        else:
            ndata = timezone.datetime(data.year, data.month, data.day,
                                      tzinfo=timezone.get_default_timezone())
        tickets = Ticket.objects.filter(created__gt=ndata-timezone.timedelta(days=1),
                                        created__lt=ndata+timezone.timedelta(days=1))
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
        system_limit = MAX_DAILY_TICKET_PER_USER
        if system_limit == 0: return False
        today_tickets = Ticket.get_user_ticket_per_day(user=user).count()
        if today_tickets < system_limit: return False
        return True


    def get_year(self):
        """
        """
        return self.created.year

    def is_assigned_to(self, office):
        """
        Ritorna True se l'ufficio passato come argomento
        è nella lista delle assegnazioni di competenza del ticket
        """
        if not office: return False
        if not office.is_active: return False
        assegnazione = TicketAssignment.objects.filter(ticket=self,
                                                       office=office).first()
        if assegnazione: return True

    def is_open(self):
        if self.is_closed: return False
        if not self.is_taken: return False
        return True

    def check_if_owner(self, user):
        """
        Ritorna True se l'utente passato come argomento ha creato il ticket
        """
        if not user: return False
        if user == self.created_by: return True

    def get_allegati_dict(self, ticket_dict={}):
        allegati_dict = {}
        if ticket_dict:
            allegati_dict = ticket_dict.get('allegati')
        else:
            json_dict = json.loads(self.modulo_compilato)
            allegati_dict = get_as_dict(compiled_module_json=json_dict).get('allegati')
        return allegati_dict

    def get_form_module(self):
        """
        Ritorna il modulo di input con cui il ticket è stato compilato
        """
        modulo = self.input_module
        return modulo

    def compiled_form(self, files=None,
                      remove_filefields=True,
                      remove_datafields=False):
        """
        Torna il form compilato senza allegati
        """
        modulo = self.get_form_module()
        if not modulo: return None
        extra_datas = {}
        extra_datas[TICKET_SUBJECT_ID] = self.subject
        extra_datas[TICKET_DESCRIPTION_ID] = self.description
        form = SavedFormContent.compiled_form(data_source=self.modulo_compilato,
                                              extra_datas=extra_datas,
                                              files=files,
                                              remove_filefields=remove_filefields,
                                              remove_datafields=remove_datafields,
                                              form_source=modulo)
        # modulo = self.get_form_module()
        # if not modulo: return False
        # json_dict = json.loads(self.modulo_compilato)
        # data = get_as_dict(compiled_module_json=json_dict,
                           # allegati=False)
        # data[TICKET_SUBJECT_ID] = self.subject
        # data[TICKET_DESCRIPTION_ID] = self.description
        # form = modulo.get_form(data=data,
                               # files=files,
                               # remove_filefields=remove_filefields,
                               # remove_datafields=remove_datafields)
        return form

    def save_data(self, subject, description, ticket_dict):
        self.subject = subject
        self.description = description
        set_as_dict(self, ticket_dict,
                    fields_to_pop=[TICKET_SUBJECT_ID,
                                   TICKET_DESCRIPTION_ID])

    def get_status(self):
        if self.is_closed: return _("Chiuso")
        if not self.is_taken: return _("In attesa di essere preso in carico")
        return _("Aperto")

    def update_log(self, user, note=None):
        if not user: return False

        # Send mail to ticket owner
        d = {'hostname': settings.HOSTNAME,
             'user': user,
             'message': note,
             'ticket': self
            }
        m_subject = _('{} - ticket {} updated'.format(settings.HOSTNAME,
                                                      self))
        send_custom_mail(subject=m_subject,
                         body=TICKET_UPDATED.format(**d),
                         recipient=user)
        # End send mail to ticket owner

        LogEntry.objects.log_action(user_id         = user.pk,
                                    content_type_id = ContentType.objects.get_for_model(self).pk,
                                    object_id       = self.pk,
                                    object_repr     = self.__str__(),
                                    action_flag     = CHANGE,
                                    change_message  = note)

    def get_assigned_to_offices(self, office_active=True):
        """
        Returns to wicth offices ticket is assigned
        """
        assignments = TicketAssignment.objects.filter(ticket=self)
        offices = []
        for assignment in assignments:
            office = assignment.office
            if not office_active: offices.append(office)
            elif office.is_active: offices.append(office)
        return offices

    def get_assigned_to_structures(self):
        """
        Returns to wich structures ticket is assigned
        """
        offices = self.get_assigned_to_offices(office_active=False)
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
        new_competence.save()
        return new_competence

    def block_competence(self, user, structure, allow_readonly=True):
        """
        """
        usertype = get_user_type(user, structure)
        if usertype == 'user': return False
        offices = []
        offices = self.get_assigned_to_offices(office_active=False)
        offices_to_disable = []
        if usertype == 'operator':
            for office in offices:
                office_employee = OrganizationalStructureOfficeEmployee.objects.filter(employee=user,
                                                                                       office=office)
                if office_employee:
                    offices_to_disable.append(office)
        elif usertype == 'manager': offices_to_disable = offices
        for off in offices_to_disable:
            if off.organizational_structure == structure:
                competence = TicketAssignment.objects.get(ticket=self,
                                                          office=off)
                if not competence.follow: continue
                competence.follow = allow_readonly
                competence.readonly = allow_readonly
                competence.save(update_fields = ['follow',
                                                 'modified',
                                                 'readonly'])
        return offices

    def get_dependences(self):
        """
        """
        # dependences = []
        t2t_list = Ticket2Ticket.objects.filter(slave_ticket=self).all()
        # for t2t in t2t_list:
            # dependences.append(t2t.master_ticket)
        # return dependences
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
        t2t_list = Ticket2Ticket.objects.filter(master_ticket=self).all()
        for t2t in t2t_list:
            dependences.append(t2t.slave_ticket)
        return dependences

    def is_closable(self):
        """
        """
        if not self.is_taken: return False
        if self.is_closed: return False
        dependences = self.get_dependences()
        task_list = self.get_task()
        if not dependences and not task_list: return True
        for dependence in dependences:
            if not dependence.master_ticket.is_closed: return False
        for task in task_list:
            if not task.is_closed: return False
        return True

    def is_valid(self):
        """
        """
        json_dict = json.loads(self.modulo_compilato)
        ticket_dict = get_as_dict(json_dict)
        if not "allegati" in ticket_dict: return True
        allegati = ticket_dict.get('allegati')
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
        return dict(PRIORITY_LEVELS).get(str(self.priority))

    def get_unread_replies(self, want_structure=False):
        # If I'm a manager/operator
        query = TicketReply.objects.filter(ticket=self,
                                           read_date=None)
        # if I'm a simple user, I want my agents replies
        if want_structure:
            replies = query.exclude(structure=None)
        else:
            replies = query.filter(structure=None)
        return replies.count()

    def _check_assignment_privileges(self, queryset):
        if not queryset: return False
        if queryset.filter(readonly=False):
            readonly_value = False
        elif queryset.filter(readonly=True):
            readonly_value = True
        d = {}
        d['follow'] = True
        d['readonly'] = readonly_value
        return d
        # return json.loads(d)

    def is_followed_in_structure(self, structure):
        if not structure: return False
        assignment = TicketAssignment.objects.filter(ticket=self,
                                                     office__organizational_structure=structure,
                                                     follow=True)
        return self._check_assignment_privileges(assignment)

    def is_followed_by_office(self, office):
        if not office: return False
        assignment = TicketAssignment.objects.filter(ticket=self,
                                                     office=office,
                                                     follow=True)
        return self._check_assignment_privileges(assignment)

    def is_followed_by_one_of_offices(self, offices):
        if not offices: return False
        assignment = TicketAssignment.objects.filter(ticket=self,
                                                     office__in=offices,
                                                     follow=True)
        return self._check_assignment_privileges(assignment)

    def __str__(self):
        return '{} ({})'.format(self.subject, self.code)


class TicketAssignment(models.Model):
    """
    Ufficio di competenza per la gestione Ticket
    """
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    office = models.ForeignKey(OrganizationalStructureOffice,
                               on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now=True)
    modified = models.DateTimeField(auto_now=True)
    note = models.TextField(blank=True, null=True)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                    on_delete=models.PROTECT,
                                    null=True)
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
        offices = OrganizationalStructureOffice.objects.filter(organizational_structure=structure)
                                                               # is_active = True)
        ticket_assignments = TicketAssignment.objects.filter(office__in=offices)
        ticket_list = []
        for assignment in ticket_assignments:
            if follow_check and not assignment.follow: continue
            ticket = assignment.ticket
            if ticket.pk not in ticket_list:
                ticket_list.append(ticket.pk)
        return ticket_list

    @staticmethod
    def get_ticket_in_office_list(office_list, follow_check=True):
        """
        """
        ticket_assignments = TicketAssignment.objects.filter(office__in=office_list)
        ticket_list = []
        for assignment in ticket_assignments:
            if follow_check and not assignment.follow: continue
            ticket = assignment.ticket
            if ticket.pk not in ticket_list:
                ticket_list.append(ticket.pk)
        return ticket_list

    def get_assegnazioni_office(self, office):
        """
        Torna la lista di ticket la cui competenza è anche
        dell'ufficio passato come argomento
        """
        assegnazioni = self.objects.filter(office=office)
        return assegnazioni

    def __str__(self):
        return '{} - {}'.format(self.ticket, self.office)


# class TicketHistory(models.Model):
    # """
    # Cronologia degli stati di avanzamento del Ticket
    # """
    # ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    # modified_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                    # on_delete=models.PROTECT,
                                    # null=True)
    # modified = models.DateTimeField(auto_now=True)
    # note = models.TextField(blank=True, null=True)

    # class Meta:
        # ordering = ["ticket", "-modified"]
        # verbose_name = _("Cronologia Stati Ticket")
        # verbose_name_plural = _("Cronologia Stati Ticket")

    # def __str__(self):
        # return '{} - {}'.format(self.ticket, self.note)


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
    attachment = models.FileField(upload_to=_reply_attachment_upload,
                                  null=True, blank=True)
    created = models.DateTimeField(auto_now=True)
    read_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                on_delete=models.SET_NULL,
                                null=True, blank=True,
                                related_name='ticket_replies_read_by')
    read_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["ticket", "created"]
        verbose_name = _("Domande/Risposte Ticket")
        verbose_name_plural = _("Domande/Risposte Ticket")

    def __str__(self):
        return '{} - {}'.format(self.ticket, self.created)


class Ticket2Ticket(models.Model):
    """
    Dipendenza Ticket da altri Ticket
    Lo Slave non può essere chiuso se ci sono Master da risolvere
    """
    slave_ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE,
                                     related_name="master")
    master_ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE,
                                      related_name="slave")
    note = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ("slave_ticket", "master_ticket")
        ordering = ["slave_ticket", "master_ticket"]
        verbose_name = _("Dipendenza Ticket")
        verbose_name_plural = _("Dipendenze Ticket")

    @staticmethod
    def master_is_already_used(ticket):
        """
        """
        relations = Ticket2Ticket.objects.filter(slave_ticket=ticket)
        if not relations: return False
        for relation in relations:
            master = relation.master_ticket
            if not master.is_closed: return True
        return False

    def __str__(self):
        return '{} - {}'.format(self.slave_ticket, self.master_ticket)


class Task(models.Model):
    """
    ToDo interno alla Struttura che può essere vincolante se associato
    a un Ticket (il Ticket non può essere chiuso se il task non è chiuso)
    """
    subject = models.CharField(max_length=255)
    code = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    created = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL,
                                   on_delete=models.SET_NULL,
                                   null=True)
    ticket = models.ForeignKey(Ticket, on_delete=models.CASCADE)
    is_closed = models.BooleanField(default=False)
    data_chiusura = models.DateTimeField(blank=True, null=True)
    motivazione_chiusura = models.TextField(blank=True, null=True)
    priority = models.IntegerField(default=0)
    attachment = models.FileField(upload_to=_task_attachment_upload,
                                  null=True, blank=True)

    class Meta:
        ordering = ["created"]
        verbose_name = _("Task")
        verbose_name_plural = _("Task")

    def get_priority(self):
        """
        """
        return dict(PRIORITY_LEVELS).get(str(self.priority))

    def update_log(self, user, note=None):
        LogEntry.objects.log_action(user_id         = user.pk,
                                    content_type_id = ContentType.objects.get_for_model(self).pk,
                                    object_id       = self.pk,
                                    object_repr     = self.__str__(),
                                    action_flag     = CHANGE,
                                    change_message  = note)

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
    # allegato = models.FileField(upload_to='allegati_clausola_partecipazione/%m-%Y/',
                                # null=True,blank=True)
    is_printable = models.BooleanField(_('Visibile nella versione stampabile'),
                                       default=False)
    is_active = models.BooleanField(_('Visibile agli utenti'), default=True)

    class Meta:
        ordering = ('ordinamento', )
        verbose_name = _('Clausola categoria ticket')
        verbose_name_plural = _('Clausole categoria ticket')

    def corpo_as_html(self):
        return text_as_html(self.text)

    def __str__(self):
        return '({}) {}'.format(self.category, self.title)
