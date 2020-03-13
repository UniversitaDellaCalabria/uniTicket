import json
import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.forms import formset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.translation import gettext as _

from django_form_builder.settings import ATTACHMENTS_DICT_PREFIX
from django_form_builder.utils import (get_as_dict,
                                       get_labeled_errors,
                                       get_POST_as_json,
                                       set_as_dict)
from organizational_area.models import (OrganizationalStructure,
                                        OrganizationalStructureOffice,)
from uni_ticket.decorators import *
from uni_ticket.forms import *
from uni_ticket.models import *
from uni_ticket.settings import *
from uni_ticket.utils import *


logger = logging.getLogger(__name__)


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
                               " di ticket: <b>{}</b>".format(MAX_DAILY_TICKET_PER_USER)))
        return redirect(reverse('uni_ticket:user_dashboard'))

    strutture = OrganizationalStructure.objects.filter(is_active=True)
    categorie = None
    template = "user/new_ticket_preload.html"
    title = _("Apri un nuovo ticket")
    sub_title = _("Seleziona la struttura")
    if structure_slug:
        struttura = get_object_or_404(OrganizationalStructure,
                                      slug=structure_slug,
                                      is_active=True)
        categorie = TicketCategory.objects.filter(organizational_structure=struttura.pk,
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
         'strutture': strutture,
         'sub_title': sub_title,
         'title': title,}
    return render(request, template, d)

@login_required
def ticket_add_new(request, structure_slug, category_slug):
    """
    Create the ticket

    :type structure_slug: String
    :type category_slug: String

    :param structure_slug: slug of structure
    :param category_slug: slug of category

    :return: render
    """
    if Ticket.number_limit_reached_by_user(request.user):
        messages.add_message(request, messages.ERROR,
                             _("Hai raggiunto il limite massimo giornaliero"
                               " di ticket: <b>{}</b>".format(MAX_DAILY_TICKET_PER_USER)))
        return redirect(reverse('uni_ticket:user_dashboard'))

    struttura = get_object_or_404(OrganizationalStructure,
                                  slug=structure_slug,
                                  is_active=True)
    categoria = get_object_or_404(TicketCategory,
                                  slug=category_slug,
                                  is_active=True)

    if not categoria.allowed_to_user(request.user):
        return custom_message(request, _("Permesso negato a questa tipologia di utente."),
                              struttura.slug)

    title = _("Nuovo ticket in {}").format(categoria)
    template = 'user/ticket_add_new.html'
    sub_title = categoria.description if categoria.description else _("Compila i campi richiesti")
    modulo = get_object_or_404(TicketCategoryModule,
                               ticket_category=categoria,
                               is_active=True)
    form = modulo.get_form(show_conditions=True)
    clausole_categoria = categoria.get_conditions()

    d={'categoria': categoria,
       'conditions': clausole_categoria,
       'form': form,
       'struttura': struttura,
       'sub_title': sub_title,
       'title': title}

    if request.POST:
        form = modulo.get_form(data=request.POST,
                               files=request.FILES,
                               show_conditions=True)
        d['form'] = form

        if form.is_valid():
            fields_to_pop = [TICKET_CONDITIONS_FIELD_ID,
                             TICKET_SUBJECT_ID,
                             TICKET_DESCRIPTION_ID]
            json_data = get_POST_as_json(request=request,
                                         fields_to_pop=fields_to_pop)
            # make a UUID based on the host ID and current time
            code = uuid_code()
            subject = form.cleaned_data[TICKET_SUBJECT_ID]
            description = form.cleaned_data[TICKET_DESCRIPTION_ID]
            ticket = Ticket(code=code,
                            subject=subject,
                            description=description,
                            modulo_compilato=json_data,
                            created_by=request.user,
                            input_module=modulo)
            ticket.save()

            # log action
            logger.info('[{}] user {} created new ticket {}'
                        ' in category {}'.format(timezone.now(),
                                                 request.user.username,
                                                 ticket,
                                                 categoria))

            # salvataggio degli allegati nella cartella relativa
            json_dict = json.loads(ticket.modulo_compilato)
            json_stored = get_as_dict(compiled_module_json=json_dict)
            if request.FILES:
                json_stored[ATTACHMENTS_DICT_PREFIX] = {}
                path_allegati = get_path_allegato(ticket)
                for key, value in request.FILES.items():
                    save_file(form.cleaned_data[key],
                              path_allegati,
                              form.cleaned_data[key]._name)
                    value = form.cleaned_data[key]._name
                    json_stored[ATTACHMENTS_DICT_PREFIX][key] = value

                    # log action
                    logger.info('[{}] attachment {} saved in {}'.format(timezone.now(),
                                                                        form.cleaned_data[key],
                                                                        path_allegati))

                set_as_dict(ticket, json_stored)

            # data di modifica
            note = _("""Inserimento nuovo ticket

                     "ticket_subject": {},
                     "ticket_description": {},
                     data: {}
                     files: {}""").format(subject,
                                          description,
                                          json_data,
                                          request.FILES)
            ticket.update_log(user=request.user,
                              note=note,
                              send_mail=False)

            # Old version. Now a category MUST have an office!
            # office = categoria.organizational_office or struttura.get_default_office()
            office = categoria.organizational_office
            ticket_assignment = TicketAssignment(ticket=ticket,
                                                 office=office,
                                                 assigned_by=request.user)
            ticket_assignment.save()

            # log action
            logger.info('[{}] ticket {} assigned to '
                        '{} office'.format(timezone.now(),
                                           ticket,
                                           office))

            ticket_detail_url = reverse('uni_ticket:ticket_detail', args=[code])

            # Send mail to ticket owner
            mail_params = {'hostname': settings.HOSTNAME,
                           'user': request.user,
                           'ticket': ticket,
                           'ticket_subject': subject,
                           'ticket_description': description,
                           'data': json_data,
                           'files': request.FILES
                          }
            m_subject = _('{} - ticket "{}" creato correttamente'.format(settings.HOSTNAME,
                                                                         ticket))
            send_custom_mail(subject=m_subject,
                             recipient=request.user,
                             body=NEW_TICKET_CREATED,
                             params=mail_params)
            # END Send mail to ticket owner

            messages.add_message(request, messages.SUCCESS,
                                 _("Ticket creato con successo "
                                   "con il codice <b>{}</b>").format(code))
            return redirect('uni_ticket:ticket_detail',
                            ticket_id=ticket.code)
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
    sub_title = _("Gestisci i tuoi ticket o creane di nuovi")
    template = "user/dashboard.html"
    tickets = Ticket.objects.filter(created_by=request.user)
    non_gestiti = tickets.filter(is_taken=False,
                                 is_closed=False)
    aperti = tickets.filter(is_taken=True, is_closed=False)
    chiusi = tickets.filter(is_closed=True)

    messages = 0
    for ticket in tickets:
        messages += ticket.get_messages_count(by_operator=True)[1]

    d = {'ticket_messages': messages,
         'priority_levels': PRIORITY_LEVELS,
         'sub_title': sub_title,
         'ticket_aperti': aperti,
         'ticket_chiusi': chiusi,
         'ticket_non_gestiti': non_gestiti,
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
    path_allegati = get_path_allegato(ticket)
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
        fields_to_pop = [TICKET_CONDITIONS_FIELD_ID]
        json_post = get_POST_as_json(request=request,
                                     fields_to_pop=fields_to_pop)
        json_response=json.loads(json_post)
        # Costruisco il form con il json dei dati inviati e tutti gli allegati
        # json_response[ATTACHMENTS_DICT_PREFIX]=allegati
        # rimuovo solo gli allegati che sono stati già inseriti
        modulo = ticket.get_form_module()
        form = modulo.get_form(data=json_response,
                               files=request.FILES,
                               remove_filefields=allegati)

        d['form'] = form

        if form.is_valid():
            if request.FILES:
                json_response[ATTACHMENTS_DICT_PREFIX] = allegati
                path_allegati = get_path_allegato(ticket)
                for key, value in request.FILES.items():
                    # form.validate_attachment(request.FILES.get(key))
                    save_file(form.cleaned_data[key],
                              path_allegati,
                              form.cleaned_data[key]._name)
                    nome_allegato = form.cleaned_data[key]._name
                    json_response[ATTACHMENTS_DICT_PREFIX]["{}".format(key)] = "{}".format(nome_allegato)
            elif allegati:
                # Se non ho aggiornato i miei allegati lasciandoli invariati rispetto
                # all'inserimento precedente
                json_response[ATTACHMENTS_DICT_PREFIX] = allegati
            # salva il modulo
            ticket.save_data(form.cleaned_data[TICKET_SUBJECT_ID],
                             form.cleaned_data[TICKET_DESCRIPTION_ID],
                             json_response)
            # data di modifica
            ticket.update_log(user=request.user,
                              note=_("Modifica ticket - data: "
                                     "{} / files: {}".format(json_post, request.FILES)))

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
    json_dict = json.loads(ticket.modulo_compilato)
    ticket_details = get_as_dict(compiled_module_json=json_dict)
    nome_file = ticket_details[ATTACHMENTS_DICT_PREFIX][attachment]

    # Rimuove il riferimento all'allegato dalla base dati
    del ticket_details[ATTACHMENTS_DICT_PREFIX][attachment]
    path_allegato = get_path_allegato(ticket)

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
    code = ticket.code
    json_dict = json.loads(ticket.modulo_compilato)
    ticket_details = get_as_dict(compiled_module_json=json_dict)
    if ATTACHMENTS_DICT_PREFIX in ticket_details:
        delete_directory(ticket_id)
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
                     body=TICKET_DELETED,
                     params=mail_params)
    # END Send mail to ticket owner

    ticket.delete()

    # log action
    logger.info('[{}] user {} deleted ticket {}'.format(timezone.now(),
                                                        request.user,
                                                        ticket))

    messages.add_message(request, messages.SUCCESS,
                         _("Ticket {} eliminato correttamente".format(code)))
    return redirect('uni_ticket:user_unassigned_ticket')

@login_required
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
    json_dict = json.loads(ticket.modulo_compilato)
    ticket_details = get_as_dict(compiled_module_json=json_dict,
                                 allegati=False,
                                 formset_management=False)
    allegati = ticket.get_allegati_dict()
    path_allegati = get_path_allegato(ticket)
    ticket_form = ticket.input_module.get_form(files=allegati,
                                               remove_filefields=False)
    priority = ticket.get_priority()

    ticket_logs = LogEntry.objects.filter(content_type_id=ContentType.objects.get_for_model(ticket).pk,
                                          object_id=ticket.pk)
    ticket_replies = TicketReply.objects.filter(ticket=ticket)
    ticket_task = Task.objects.filter(ticket=ticket)
    ticket_dependences = ticket.get_dependences()
    title = _("Dettaglio ticket")
    sub_title = ticket
    assigned_to = []
    ticket_assignments = TicketAssignment.objects.filter(ticket=ticket)

    d={'allegati': allegati,
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
    if ticket.is_open():
        agent_replies = ticket_replies.exclude(owner=ticket.created_by,
                                               structure=None).filter(read_by=None)
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
            ticket_reply.text = form.cleaned_data['text']
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
                           'user': request.user
                          }
            m_subject = _('{} - ticket {} messaggio inviato'.format(settings.HOSTNAME,
                                                                    ticket))
            send_custom_mail(subject=m_subject,
                             recipient=request.user,
                             body=USER_TICKET_MESSAGE,
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
    # Se il ticket non è chiudibile (per dipendenze attive)
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
            ticket.motivazione_chiusura = motivazione
            ticket.data_chiusura = timezone.now()
            ticket.save(update_fields = ['is_closed',
                                         'motivazione_chiusura',
                                         'data_chiusura'])
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
