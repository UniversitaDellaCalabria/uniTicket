import os
import json
import logging
import shutil

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.forms import formset_factory
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.html import escape, strip_tags
from django.utils.translation import gettext as _

from django_form_builder.utils import (get_as_dict,
                                       get_labeled_errors,
                                       get_POST_as_json,
                                       set_as_dict)
from organizational_area.models import (OrganizationalStructure,
                                        OrganizationalStructureOffice,
                                        OrganizationalStructureOfficeEmployee,)
from uni_ticket.decorators import *
from uni_ticket.forms import *
from uni_ticket.models import *
from uni_ticket.utils import *

logger = logging.getLogger(__name__)


# assign category default tasks to new ticket created by user
def _assign_default_tasks_to_new_ticket(ticket, category, log_user):
    tasks = category.get_tasks(is_active=True)
    for task in tasks:
        ticket_task = Task()
        ticket_task.ticket = ticket
        ticket_task.subject = task.subject
        ticket_task.description = task.description
        ticket_task.priority = task.priority
        ticket_task.created_by = task.created_by
        ticket_task.code = uuid_code()
        ticket_task.attachment = task.attachment
        ticket_task.save()

        # copy category task attachments in ticket task folder
        if task.attachment:
            source = '{}/{}'.format(settings.MEDIA_ROOT,
                                    task.get_folder())
            destination = '{}/{}'.format(settings.MEDIA_ROOT,
                                         ticket_task.get_folder())
            try:
                if os.path.exists(source):
                    shutil.copytree(source, destination)
            except:
                logger.info('[{}] {} try to copy not existent folder {}'
                            ''.format(timezone.now(),
                                      log_user,
                                      source))

# close ticket as soon as opened if it's a notification ticket
def _close_notification_ticket(ticket, user, operator, ticket_assignment):
    # close ticket
    ticket.is_closed = True
    ticket.closed_date = timezone.now()
    ticket.closed_by = user
    ticket.save(update_fields=['is_closed',
                               'closed_date',
                               'closed_by'])

    # assign to an operator
    ticket_assignment.taken_date = timezone.now()
    ticket_assignment.taken_by = operator
    ticket_assignment.save(update_fields=['taken_date', 'taken_by'])

# save attachments of new ticket
def _save_new_ticket_attachments(ticket,
                                 json_stored,
                                 form,
                                 request_files):
    if request_files:
        json_stored[settings.ATTACHMENTS_DICT_PREFIX] = {}
        path_allegati = get_path(ticket.get_folder())
        for key, value in request_files.items():
            save_file(form.cleaned_data[key],
                      path_allegati,
                      form.cleaned_data[key]._name)
            value = form.cleaned_data[key]._name
            json_stored[settings.ATTACHMENTS_DICT_PREFIX][key] = value

            # log action
            logger.info('[{}] attachment {} saved in {}'.format(timezone.now(),
                                                                form.cleaned_data[key],
                                                                path_allegati))

        set_as_dict(ticket, json_stored)

@login_required
def ticket_new_preload(request, structure_slug=None):
    """
    Choose the OrganizationalStructure and the category of the ticket

    :type structure_slug: String

    :param structure_slug: slug of structure

    :return: render
    """
    if Ticket.number_limit_reached_by_user(request.user):
        messages.add_message(request, messages.ERROR,
                             _("Hai raggiunto il limite massimo giornaliero"
                               " di ticket: <b>{}</b>".format(settings.MAX_DAILY_TICKET_PER_USER)))
        return redirect(reverse('uni_ticket:user_dashboard'))

    strutture = OrganizationalStructure.objects.filter(is_active=True)
    categorie = None
    template = "user/new_ticket_preload.html"
    title = _("Apri un nuovo ticket")
    sub_title = _("Seleziona la struttura")
    structure = None
    if structure_slug:
        structure = get_object_or_404(OrganizationalStructure,
                                      slug=structure_slug,
                                      is_active=True)
        categorie = TicketCategory.objects.filter(organizational_structure=structure,
                                                  is_active=True)
        # User roles
        is_employee = user_is_employee(request.user)
        is_user = user_is_in_organization(request.user)

        if is_employee and is_user:
            categorie = categorie.filter(Q(allow_employee=True) |
                                         Q(allow_user=True) |
                                         Q(allow_guest=True))
        elif is_employee:
            categorie = categorie.filter(Q(allow_employee=True) |
                                         Q(allow_guest=True))
        elif is_user:
            categorie = categorie.filter(Q(allow_user=True) |
                                         Q(allow_guest=True))
        else:
            categorie = categorie.filter(allow_guest=True)

        sub_title = _("Seleziona la Categoria")
    d = {'categorie': categorie,
         'structure_slug': structure_slug,
         'chosen_structure': structure,
         'strutture': strutture,
         'sub_title': sub_title,
         'title': title,}
    return render(request, template, d)

# @login_required
def ticket_add_new(request, structure_slug, category_slug):
    """
    Create the ticket

    :type structure_slug: String
    :type category_slug: String

    :param structure_slug: slug of structure
    :param category_slug: slug of category

    :return: render
    """
    struttura = get_object_or_404(OrganizationalStructure,
                                  slug=structure_slug,
                                  is_active=True)
    category = get_object_or_404(TicketCategory,
                                 slug=category_slug)

    if not category.is_active:
        return custom_message(request, category.not_available_message,
                              status=404)

    # if anonymous user and category only for logged users
    if not category.allow_anonymous and not request.user.is_authenticated:
        return redirect('{}?next={}'.format(settings.LOGIN_URL, request.path))

    # is user is authenticated
    if request.user.is_authenticated:
        # check ticket number limit
        if Ticket.number_limit_reached_by_user(request.user):
            messages.add_message(request, messages.ERROR,
                                 _("Hai raggiunto il limite massimo giornaliero"
                                   " di ticket: <b>{}</b>"
                                   "".format(settings.MAX_DAILY_TICKET_PER_USER)))
            return redirect('uni_ticket:user_dashboard')
        # check if user is allowed to access this category
        if not category.allowed_to_user(request.user):
            return custom_message(request, _("Permesso negato a questa tipologia di utente."))

    title = category
    template = 'user/ticket_add_new.html'
    sub_title = category.description if category.description else _("Compila i campi richiesti")
    modulo = get_object_or_404(TicketCategoryModule,
                               ticket_category=category,
                               is_active=True)
    form = modulo.get_form(show_conditions=True,
                           current_user=request.user)
    clausole_categoria = category.get_conditions()
    d={'categoria': category,
       'category_conditions': clausole_categoria,
       'form': form,
       'struttura': struttura,
       'sub_title': '{} - {}'.format(struttura, sub_title),
       'title': title}

    # after form submit
    if request.POST:
        form = modulo.get_form(data=request.POST,
                               files=request.FILES,
                               show_conditions=True,
                               current_user=request.user)
        d['form'] = form

        if form.is_valid():
            fields_to_pop = [settings.TICKET_CONDITIONS_FIELD_ID,
                             settings.TICKET_SUBJECT_ID,
                             settings.TICKET_DESCRIPTION_ID,
                             settings.TICKET_CAPTCHA_ID,
                             settings.TICKET_CAPTCHA_HIDDEN_ID]
            json_data = get_POST_as_json(request=request,
                                         fields_to_pop=fields_to_pop)
            # make a UUID based on the host ID and current time
            code = uuid_code()
            subject = form.cleaned_data[settings.TICKET_SUBJECT_ID]
            description = form.cleaned_data[settings.TICKET_DESCRIPTION_ID]

            # destination office
            office = category.organizational_office

            # take a random operator (or manager)
            # only if category is_notify or user is anonymous
            random_office_operator = None
            if category.is_notify or not request.user.is_authenticated:
                # get random operator from the office
                random_office_operator = OrganizationalStructureOfficeEmployee.get_default_operator_or_manager(office)

            # set users (for current operation and for log)
            current_user = request.user if request.user.is_authenticated else random_office_operator
            log_user = request.user.username if request.user.is_authenticated else 'anonymous'
            # create ticket
            ticket = Ticket(code=code,
                            subject=subject,
                            description=description,
                            modulo_compilato=json_data,
                            created_by=current_user,
                            input_module=modulo)
            ticket.save()

            # log action
            logger.info('[{}] user {} created new ticket {}'
                        ' in category {}'.format(timezone.now(),
                                                 log_user,
                                                 ticket,
                                                 category))

            # salvataggio degli allegati nella cartella relativa
            json_dict = json.loads(json_data)
            json_stored = get_as_dict(compiled_module_json=json_dict)
            _save_new_ticket_attachments(ticket=ticket,
                                         json_stored=json_stored,
                                         form=form,
                                         request_files=request.FILES)

            ticket_assignment = TicketAssignment(ticket=ticket,
                                                 office=office)
            ticket_assignment.save()

            # if it's a notification ticket, take and close the ticket
            if category.is_notify:
                _close_notification_ticket(ticket=ticket,
                                           user=current_user,
                                           operator=random_office_operator,
                                           ticket_assignment=ticket_assignment)

            # log action
            logger.info('[{}] ticket {} assigned to '
                        '{} office'.format(timezone.now(),
                                           ticket,
                                           office))

            # category default tasks
            _assign_default_tasks_to_new_ticket(ticket=ticket,
                                                category=category,
                                                log_user=log_user)

            ticket_message = ticket.input_module.ticket_category.confirm_message_text or \
                             settings.NEW_TICKET_CREATED_ALERT
            compiled_message = ticket_message.format(ticket.subject)
            messages.add_message(request,
                                 messages.SUCCESS,
                                 compiled_message
                                )
            # if user is authenticated send mail and redirect to ticket page
            if request.user.is_authenticated:
                # Send mail to ticket owner
                mail_params = {'hostname': settings.HOSTNAME,
                               'user': request.user,
                               'ticket': ticket.code,
                               'ticket_subject': subject,
                               'url': request.build_absolute_uri(reverse('uni_ticket:ticket_detail',
                                                                 kwargs={'ticket_id': ticket.code})),
                                'added_text': compiled_message
                              }

                m_subject = _('{} - {}'.format(settings.HOSTNAME,
                                               compiled_message))
                m_subject = m_subject[:80] + (m_subject[80:] and '...')

                send_custom_mail(subject=m_subject,
                                 recipient=request.user,
                                 body=settings.NEW_TICKET_CREATED,
                                 params=mail_params)
                # END Send mail to ticket owner
                return redirect('uni_ticket:ticket_detail',
                                ticket_id=ticket.code)
            else:
                return redirect('uni_ticket:add_new_ticket',
                                structure_slug=structure_slug,
                                category_slug=category_slug)
        else:
            for k,v in get_labeled_errors(form).items():
                messages.add_message(request, messages.ERROR,
                                     "<b>{}</b>: {}".format(k, strip_tags(v)))
    return render(request, template, d)

@login_required
def dashboard(request):
    """
    Dashboard of user, with tickets list

    :return: render
    """
    # Ci pensa datatables a popolare la tabella
    title =_("Pannello di controllo")
    sub_title = _("Gestisci i tuoi ticket o aprine di nuovi")
    template = "user/dashboard.html"
    tickets = Ticket.objects.filter(created_by=request.user)
    not_closed = tickets.filter(is_closed=False)
    # unassigned = []
    # opened = []
    unassigned = 0
    opened = 0
    for nc in not_closed:
        if nc.has_been_taken():
            # opened.append(nc)
            opened += 1
        else:
            # unassigned.append(nc)
            unassigned += 1
    # chiusi = tickets.filter(is_closed=True)
    chiusi = tickets.filter(is_closed=True).count()

    messages = 0
    for ticket in tickets:
        messages += ticket.get_messages_count(by_operator=True)[1]

    d = {'ticket_messages': messages,
         'priority_levels': settings.PRIORITY_LEVELS,
         'sub_title': sub_title,
         'ticket_aperti': opened,
         'ticket_chiusi': chiusi,
         'ticket_non_gestiti': unassigned,
         'title': title,}

    return render(request, template, d)

@login_required
@is_the_owner
@ticket_is_not_taken_and_not_closed
def ticket_edit(request, ticket_id):
    """
    Edit ticket details while it is unassigned
    Note: formset validation is in widget (._fill_body method)

    :type ticket_id: String

    :param ticket_id: ticket code

    :return: render
    """
    ticket = get_object_or_404(Ticket, code=ticket_id)
    categoria = ticket.input_module.ticket_category
    title = _("Modifica ticket")
    sub_title = ticket
    allegati = ticket.get_allegati_dict()
    path_allegati = get_path(ticket.get_folder())
    form = ticket.compiled_form(files=None, remove_filefields=allegati)
    form_allegati = ticket.compiled_form(files=None,
                                         remove_filefields=False,
                                         remove_datafields=True)
    template = "user/ticket_edit.html"
    d = {'allegati': allegati,
         'categoria': categoria,
         'form': form,
         'form_allegati': form_allegati,
         'path_allegati': path_allegati,
         'sub_title': sub_title,
         'ticket': ticket,
         'title': title,}
    if request.method == 'POST':
        fields_to_pop = [settings.TICKET_CONDITIONS_FIELD_ID]
        json_post = get_POST_as_json(request=request,
                                     fields_to_pop=fields_to_pop)
        json_response=json.loads(json_post)
        # Costruisco il form con il json dei dati inviati e tutti gli allegati
        # json_response[settings.ATTACHMENTS_DICT_PREFIX]=allegati
        # rimuovo solo gli allegati che sono stati già inseriti
        modulo = ticket.get_form_module()
        form = modulo.get_form(data=json_response,
                               files=request.FILES,
                               remove_filefields=allegati)

        d['form'] = form

        if form.is_valid():
            if request.FILES:
                json_response[settings.ATTACHMENTS_DICT_PREFIX] = allegati
                path_allegati = get_path(ticket.get_folder())
                for key, value in request.FILES.items():
                    nome_allegato = form.cleaned_data[key]._name
                    # form.validate_attachment(request.FILES.get(key))
                    save_file(form.cleaned_data[key],
                              path_allegati,
                              nome_allegato)
                    json_response[settings.ATTACHMENTS_DICT_PREFIX]["{}".format(key)] = "{}".format(nome_allegato)
            elif allegati:
                # Se non ho aggiornato i miei allegati lasciandoli invariati rispetto
                # all'inserimento precedente
                json_response[settings.ATTACHMENTS_DICT_PREFIX] = allegati
            # salva il modulo
            ticket.save_data(form.cleaned_data[settings.TICKET_SUBJECT_ID],
                             form.cleaned_data[settings.TICKET_DESCRIPTION_ID],
                             json_response)
            # data di modifica
            ticket.update_log(user=request.user,
                              note=_("Ticket modificato"))

            # log action
            logger.info('[{}] user {} edited ticket {}'.format(timezone.now(),
                                                               request.user,
                                                               ticket))

            # Allega il messaggio al redirect
            messages.add_message(request, messages.SUCCESS,
                                 _("Modifica effettuata con successo"))
            return redirect('uni_ticket:ticket_edit', ticket_id=ticket_id)
        else:
            for k,v in get_labeled_errors(form).items():
                messages.add_message(request, messages.ERROR,
                                     "<b>{}</b>: {}".format(k, strip_tags(v)))

    return render(request, template, d)

@login_required
@is_the_owner
@ticket_is_not_taken_and_not_closed
def delete_my_attachment(request, ticket_id, attachment):
    """
    Delete ticket attachment while it is unassigned
    Note: it must be called by a dialogbox with user confirmation

    :type ticket_id: String
    :type attachment: String

    :param ticket_id: ticket code
    :param attachment: attachment name

    :return: redirect
    """
    ticket = get_object_or_404(Ticket, code=ticket_id)
    json_dict = ticket.get_modulo_compilato()
    ticket_details = get_as_dict(compiled_module_json=json_dict)
    nome_file = ticket_details[settings.ATTACHMENTS_DICT_PREFIX][attachment]

    # Rimuove il riferimento all'allegato dalla base dati
    del ticket_details[settings.ATTACHMENTS_DICT_PREFIX][attachment]
    path_allegato = get_path(ticket.get_folder())

    # Rimuove l'allegato dal disco
    delete_file(file_name=nome_file, path=path_allegato)

    # log action
    logger.info('[{}] user {} deleted file {}'.format(timezone.now(),
                                                      request.user.username,
                                                      path_allegato))

    set_as_dict(ticket, ticket_details)
    allegati = ticket.get_allegati_dict(ticket_dict=ticket_details)
    ticket.update_log(user=request.user,
                      note=_("Elimina allegato"))

    # log action
    logger.info('[{}] user {} deleted attachment '
                '{} for ticket {}'.format(timezone.now(),
                                          request.user.username,
                                          nome_file,
                                          ticket))

    messages.add_message(request, messages.SUCCESS,
                         _("Allegato eliminato correttamente"))
    return redirect('uni_ticket:ticket_edit', ticket_id=ticket_id)

@login_required
@is_the_owner
@ticket_is_not_taken_and_not_closed
def ticket_delete(request, ticket_id):
    """
    Delete ticket while it is unassigned
    Note: it must be called by a dialogbox with user confirmation

    :type ticket_id: String

    :param ticket_id: ticket code

    :return: redirect
    """
    ticket = get_object_or_404(Ticket, code=ticket_id)
    ticket_assignment = TicketAssignment.objects.filter(ticket=ticket).first()

    # log action
    logger.info('[{}] ticket {} assignment'
                ' to office {}'
                ' has been deleted'
                ' by user {}'.format(timezone.now(),
                                     ticket,
                                     ticket_assignment.office,
                                     request.user))

    ticket_assignment.delete()

    # Send mail to ticket owner
    mail_params = {'hostname': settings.HOSTNAME,
                   'user': request.user,
                   'status': _("eliminato"),
                   'ticket': ticket
                  }
    m_subject = _('{} - ticket {} eliminato'.format(settings.HOSTNAME,
                                                    ticket))

    send_custom_mail(subject=m_subject,
                     recipient=request.user,
                     body=settings.TICKET_DELETED,
                     params=mail_params)
    # END Send mail to ticket owner

    ticket.delete()

    # log action
    logger.info('[{}] user {} deleted ticket {}'.format(timezone.now(),
                                                        request.user,
                                                        ticket))

    messages.add_message(request, messages.SUCCESS,
                         _("Ticket {} eliminato correttamente".format(ticket.code)))
    return redirect('uni_ticket:user_unassigned_ticket')

# @login_required
# @is_the_owner
# decorators in urls.py (print view call this view but with different decorators)
def ticket_detail(request, ticket_id, template='user/ticket_detail.html'):
    """
    Shows ticket details

    :type ticket_id: String
    :type template: String

    :param ticket_id: ticket code
    :param attachment: template to user (can change if specified)

    :return: render
    """
    ticket = get_object_or_404(Ticket, code=ticket_id)
    modulo_compilato = ticket.get_modulo_compilato()
    ticket_details = get_as_dict(compiled_module_json=modulo_compilato,
                                 allegati=False,
                                 formset_management=False)
    allegati = ticket.get_allegati_dict()
    path_allegati = get_path(ticket.get_folder())
    ticket_form = ticket.input_module.get_form(files=allegati,
                                               remove_filefields=False)
    priority = ticket.get_priority()

    ticket_logs = LogEntry.objects.filter(content_type_id=ContentType.objects.get_for_model(ticket).pk,
                                          object_id=ticket.pk)
    ticket_replies = TicketReply.objects.filter(ticket=ticket)
    ticket_task = Task.objects.filter(ticket=ticket)
    ticket_dependences = ticket.get_dependences()
    title = ticket.subject
    sub_title = ticket.code
    assigned_to = []
    ticket_assignments = TicketAssignment.objects.filter(ticket=ticket)

    category_conditions = ticket.input_module.ticket_category.get_conditions(is_printable=True)

    d={'allegati': allegati,
       'category_conditions': category_conditions,
       'dependences': ticket_dependences,
       'details': ticket_details,
       'path_allegati': path_allegati,
       'priority': priority,
       'sub_title': sub_title,
       'ticket': ticket,
       'ticket_assignments': ticket_assignments,
       'ticket_form': ticket_form,
       'logs': ticket_logs,
       'ticket_task': ticket_task,
       'title': title,}
    template = template
    return render(request, template, d)

@login_required
def ticket_url(request):
    """
    Fake URL to build datatables ticket details link on click (href)
    """
    return custom_message(request, _("Permesso negato"))

@login_required
@is_the_owner
def ticket_message(request, ticket_id):
    """
    Ticket messages page

    :param ticket_id: String

    :type ticket_id: ticket code

    :return: render
    """
    ticket = get_object_or_404(Ticket, code=ticket_id)
    title = _("Messaggi")
    sub_title = ticket
    # Conversazione utente-operatori
    ticket_replies = TicketReply.objects.filter(ticket=ticket)
    form = ReplyForm()
    # if ticket.is_open():
    agent_replies = ticket_replies.filter(read_by=None).exclude(structure=None)
    for reply in agent_replies:
        reply.read_by = request.user
        reply.read_date = timezone.now()
        reply.save(update_fields = ['read_by', 'read_date'])

    if request.method == 'POST':
        if not ticket.is_open():
            # log action
            logger.info('[{}] user {} tried to submit'
                        ' a message for the not opened ticket {}'.format(timezone.now(),
                                                                        request.user,
                                                                        ticket))
            return custom_message(request, _("Il ticket non è modificabile"))
        form = ReplyForm(request.POST, request.FILES)
        if form.is_valid():
            ticket_reply = TicketReply()
            ticket_reply.subject = form.cleaned_data['subject']
            ticket_reply.text = get_text_with_hrefs(escape(form.cleaned_data['text']))
            ticket_reply.attachment = form.cleaned_data['attachment']
            ticket_reply.ticket = ticket
            ticket_reply.owner = request.user
            ticket_reply.save()

            # log action
            logger.info('[{}] user {} submitted a message'
                        ' for ticket {}'.format(timezone.now(),
                                                request.user,
                                                ticket))

            # Send mail to ticket owner
            mail_params = {'hostname': settings.HOSTNAME,
                           'status': _("inviato"),
                           'ticket': ticket,
                           'user': request.user,
                           'url': request.build_absolute_uri(reverse('uni_ticket:ticket_message',
                                                             kwargs={'ticket_id': ticket.code}))
                          }
            m_subject = _('{} - ticket {} messaggio inviato'.format(settings.HOSTNAME,
                                                                    ticket))
            send_custom_mail(subject=m_subject,
                             recipient=request.user,
                             body=settings.USER_TICKET_MESSAGE,
                             params=mail_params)
            # END Send mail to ticket owner

            messages.add_message(request, messages.SUCCESS,
                                 _("Messaggio inviato con successo"))
            return redirect('uni_ticket:ticket_message',
                            ticket_id=ticket_id)
        else:
            for k,v in get_labeled_errors(form).items():
                messages.add_message(request, messages.ERROR,
                                     "<b>{}</b>: {}".format(k, strip_tags(v)))
    d={'form': form,
       'sub_title': sub_title,
       'ticket': ticket,
       'ticket_replies': ticket_replies,
       'title': title,}
    template='user/ticket_assistance.html'
    return render(request, template, d)

@login_required
@is_the_owner
def task_detail(request, ticket_id, task_id):
    """
    Task details page

    :param ticket_id: String
    :param task_id: String

    :type ticket_id: ticket code
    :type task_id: task code

    :return: render
    """
    ticket = get_object_or_404(Ticket, code=ticket_id)
    task = get_object_or_404(Task, code=task_id, ticket=ticket)
    title = _("Dettaglio task")
    d={'sub_title': task,
       'task': task,
       'title': title}
    template = "task_detail.html"
    return render(request, template, d)

@login_required
@is_the_owner
def ticket_close(request, ticket_id):
    """
    Ticket closing by owner user

    :param ticket_id: String

    :type ticket_id: ticket code

    :return: render
    """
    ticket = get_object_or_404(Ticket, code=ticket_id)
    if ticket.is_closed:
        # log action
        logger.info('[{}] user {} tried to close '
                    ' the already closed ticket {}'.format(timezone.now(),
                                                           request.user,
                                                           ticket))

        return custom_message(request, _("Il ticket è già chiuso!"))

    title = _('Chiusura del ticket')
    sub_title = ticket
    form = ChiusuraForm()
    if request.method=='POST':
        form = ChiusuraForm(request.POST)
        if form.is_valid():
            motivazione = form.cleaned_data['note']
            ticket.is_closed = True
            ticket.closing_reason = motivazione
            ticket.closed_date = timezone.now()
            ticket.save(update_fields = ['is_closed',
                                         'closing_reason',
                                         'closed_date'])
            ticket.update_log(user=request.user,
                              note=_("Chiusura ticket: {}".format(motivazione)))
            messages.add_message(request, messages.SUCCESS,
                                 _("Ticket {} chiuso correttamente".format(ticket)))

            # log action
            logger.info('[{}] user {} closed ticket {}'.format(timezone.now(),
                                                               request.user,
                                                               ticket))

            return redirect('uni_ticket:ticket_detail', ticket.code)
        else:
            for k,v in get_labeled_errors(form).items():
                messages.add_message(request, messages.ERROR,
                                     "<b>{}</b>: {}".format(k, strip_tags(v)))

    template = "user/ticket_close.html"
    d = {'form': form,
         'sub_title': sub_title,
         'ticket': ticket,
         'title': title,}
    return render(request, template, d)

@login_required
def chat_new_preload(request, structure_slug=None):
    """
    Choose the OrganizationalStructure and the category of the ticket

    :type structure_slug: String

    :param structure_slug: slug of structure

    :return: render
    """
    strutture = OrganizationalStructure.objects.filter(is_active=True)
    template = "user/new_chat_preload.html"
    title = _("Avvia chat con un operatore")
    sub_title = _("Seleziona la struttura")
    if structure_slug:
        struttura = get_object_or_404(OrganizationalStructure,
                                      slug=structure_slug,
                                      is_active=True)
        sub_title = struttura
    d = {'structure_slug': structure_slug,
         'strutture': strutture,
         'sub_title': sub_title,
         'title': title,}
    return render(request, template, d)

@login_required
def ticket_clone(request, ticket_id):
    master_ticket = get_object_or_404(Ticket,
                                      code=ticket_id,
                                      created_by=request.user)
    # if ticket is not closed and owner has closed it
    if not master_ticket.is_closed:
       return custom_message(request, _("Operazione non permessa. "
                                        "Il ticket è ancora attivo"))

    # if ticket module is out of date
    if not master_ticket.input_module.is_active:
           return custom_message(request, _("Il modulo che stai cercando "
                                            "di usare non è più attivo."))

    category = master_ticket.input_module.ticket_category
    data = master_ticket.get_modulo_compilato()
    data['ticket_subject'] = master_ticket.subject
    data['ticket_description'] = master_ticket.description
    form = master_ticket.input_module.get_form(data=data, show_conditions=True)
    title = category
    template = 'user/ticket_add_new.html'
    sub_title = category.description if category.description else _("Compila i campi richiesti")
    clausole_categoria = category.get_conditions()

    d={'categoria': category,
       'category_conditions': clausole_categoria,
       'form': form,
       'struttura': category.organizational_structure,
       'sub_title': '{} - {}'.format(category.organizational_structure,
                                     sub_title),
       'title': title}

    if request.POST:
        form = master_ticket.input_module.get_form(data=request.POST,
                                                   files=request.FILES,
                                                   show_conditions=True)
        d['form'] = form

        if form.is_valid():
            fields_to_pop = [settings.TICKET_CONDITIONS_FIELD_ID,
                             settings.TICKET_SUBJECT_ID,
                             settings.TICKET_DESCRIPTION_ID]
            json_data = get_POST_as_json(request=request,
                                         fields_to_pop=fields_to_pop)
            # make a UUID based on the host ID and current time
            code = uuid_code()
            subject = form.cleaned_data[settings.TICKET_SUBJECT_ID]
            description = form.cleaned_data[settings.TICKET_DESCRIPTION_ID]
            ticket = Ticket(code=code,
                            subject=subject,
                            description=description,
                            modulo_compilato=json_data,
                            created_by=request.user,
                            input_module=master_ticket.input_module)
            ticket.save()

            # log action
            logger.info('[{}] user {} created new ticket {}'
                        ' in category {}'.format(timezone.now(),
                                                 request.user.username,
                                                 ticket,
                                                 category))

            # salvataggio degli allegati nella cartella relativa
            json_dict = ticket.get_modulo_compilato()
            json_stored = get_as_dict(compiled_module_json=json_dict)
            _save_new_ticket_attachments(ticket=ticket,
                                         json_stored=json_stored,
                                         form=form,
                                         request_files=request.FILES)

            # Old version. Now a category MUST have an office!
            # office = categoria.organizational_office or struttura.get_default_office()
            office = category.organizational_office
            ticket_assignment = TicketAssignment(ticket=ticket,
                                                 office=office)
                                                 # assigned_by=request.user)
            ticket_assignment.save()

            if category.is_notify:
                random_office_operator = OrganizationalStructureOfficeEmployee.get_default_operator_or_manager(office)

                # if ticket is a notify, take the ticket
                _close_notification_ticket(ticket=ticket,
                                           user=request.user,
                                           operator=random_office_operator,
                                           ticket_assignment=ticket_assignment)

            # log action
            logger.info('[{}] ticket {} assigned to '
                        '{} office'.format(timezone.now(),
                                           ticket,
                                           office))

            # category default tasks
            _assign_default_tasks_to_new_ticket(ticket=ticket,
                                                category=category,
                                                log_user=request.user)

            # Send mail to ticket owner
            ticket_message = ticket.input_module.ticket_category.confirm_message_text or \
                             settings.NEW_TICKET_CREATED_ALERT
            compiled_message = ticket_message.format(ticket.subject)

            mail_params = {'hostname': settings.HOSTNAME,
                           'user': request.user,
                           'ticket': ticket.code,
                           'ticket_subject': subject,
                           'url': request.build_absolute_uri(reverse('uni_ticket:ticket_detail',
                                                             kwargs={'ticket_id': ticket.code})),
                            'added_text': compiled_message
                          }

            m_subject = _('{} - {}'.format(settings.HOSTNAME,
                                           compiled_message))
            m_subject = m_subject[:80] + (m_subject[80:] and '...')

            send_custom_mail(subject=m_subject,
                             recipient=request.user,
                             body=settings.NEW_TICKET_CREATED,
                             params=mail_params)
            # END Send mail to ticket owner

            messages.add_message(request, messages.SUCCESS,
                                 compiled_message)
            return redirect('uni_ticket:ticket_detail',
                            ticket_id=ticket.code)
        else:
            for k,v in get_labeled_errors(form).items():
                messages.add_message(request, messages.ERROR,
                                     "<b>{}</b>: {}".format(k, strip_tags(v)))
    return render(request, template, d)
