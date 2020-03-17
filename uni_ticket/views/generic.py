import json
import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import (HttpResponse,
                         HttpResponseRedirect,
                         Http404,
                         JsonResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext as _

from django_form_builder.settings import ATTACHMENTS_DICT_PREFIX
from django_form_builder.utils import get_as_dict
from organizational_area.models import OrganizationalStructure

from uni_ticket.decorators import *
from uni_ticket.models import *
from uni_ticket.settings import *
from uni_ticket.utils import *
from uni_ticket.views import user


@login_required
def manage(request, structure_slug=None):
    """
    Makes URL redirect to manage a structure depending of user role

    :type structure_slug: String

    :param structure_slug: slug of structure to manage

    :return: redirect
    """
    if not structure_slug: return redirect('uni_ticket:user_dashboard')
    structure = get_object_or_404(OrganizationalStructure,
                                  slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    if user_type == 'user': return redirect('uni_ticket:user_dashboard')
    return redirect('uni_ticket:{}_dashboard'.format(user_type),
                    structure_slug=structure_slug)

@login_required
@has_access_to_ticket
def download_attachment(request, ticket_id, attachment, ticket):
    """
    Downloads ticket attachment

    :type ticket_id:String
    :type attachment: String
    :type ticket: Ticket (from @has_access_to_ticket)

    :param ticket_id: ticket code
    :param attachment: attachment name
    :param ticket: ticket object (from @has_access_to_ticket)

    :return: file
    """
    # get ticket json dictionary
    json_dict = json.loads(ticket.modulo_compilato)
    ticket_details = get_as_dict(compiled_module_json=json_dict)
    if attachment:
        # get ticket attachments
        attachments = ticket_details[ATTACHMENTS_DICT_PREFIX]
        # get the attachment
        documento = attachments[attachment]
        # get ticket folder path
        path_allegato = get_path_allegato(ticket)
        # get file
        result = download_file(path_allegato, documento)
        return result
    raise Http404

@login_required
@has_access_to_ticket
def download_message_attachment(request, ticket_id, reply_id, ticket):
    """
    Downloads ticket message attachment

    :type ticket_id: String
    :type reply_id: String
    :type ticket: Ticket (from @has_access_to_ticket)

    :param ticket_id: ticket code
    :param reply_id: message id
    :param ticket: ticket object (from @has_access_to_ticket)

    :return: file
    """
    # get the message
    message = get_object_or_404(TicketReply, pk=reply_id)
    # if message has attachment
    if message.attachment:
        # get ticket folder path
        path_allegato = get_path_allegato(ticket)
        # get file
        result = download_file("{}/{}".format(path_allegato,
                                              TICKET_MESSAGES_ATTACHMENT_SUBFOLDER),
                               os.path.basename(message.attachment.name))
        return result
    raise Http404

@login_required
@has_access_to_ticket
def download_task_attachment(request, ticket_id, task_id, ticket):
    """
    Downloads ticket message attachment

    :type ticket_id: String
    :type task_id: String
    :type ticket: Ticket (from @has_access_to_ticket)

    :param ticket_id: ticket code
    :param task_id: task code
    :param ticket: ticket object (from @has_access_to_ticket)

    :return: file
    """
    # get task
    task = get_object_or_404(Task, code=task_id)
    # if task has attachment
    if task.attachment:
        # get ticket folder path
        path_allegato = get_path_allegato(ticket)
        # get file
        result = download_file("{}/{}/{}".format(path_allegato,
                                                 TICKET_TASK_ATTACHMENT_SUBFOLDER,
                                                 task_id),
                               os.path.basename(task.attachment.name))
        return result
    raise Http404

@login_required
def opened_ticket(request, structure_slug=None,
                  structure=None, office_employee=None):
    """
    Gets opened tickets list (requires HTML datatable in template)

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_manager/@is_operator)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param structure: structure object (from @is_manager/@is_operator)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    title = _("Ticket assegnati")
    user_type = get_user_type(request.user, structure)
    template = "{}/opened_ticket.html".format(user_type)
    d = {'structure': structure,
         'sub_title': structure,
         'title': title,}
    return render(request, template, d)

@login_required
def unassigned_ticket(request, structure_slug=None,
                      structure=None, office_employee=None):
    """
    Gets unassigned tickets list (requires HTML datatable in template)

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_manager/@is_operator)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param structure: structure object (from @is_manager/@is_operator)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    title = _("Ticket aperti")
    user_type = get_user_type(request.user, structure)
    template = "{}/unassigned_ticket.html".format(user_type)
    d = {'structure': structure,
         'sub_title': structure,
         'title': title,}
    return render(request, template, d)

@login_required
def closed_ticket(request, structure_slug=None,
                  structure=None, office_employee=None):
    """
    Gets closed tickets list (requires HTML datatable in template)

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_manager/@is_operator)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param structure: structure object (from @is_manager/@is_operator)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    title = _("Ticket chiusi")
    user_type = get_user_type(request.user, structure)
    template = "{}/closed_ticket.html".format(user_type)
    d = {'structure': structure,
         'sub_title': structure,
         'title': title,}
    return render(request, template, d)

@login_required
def email_notify_change(request):
    if request.method == 'POST':
        data = {}
        user = request.user
        email = user.email
        if not email:
            data['error'] = _("Nessuna e-mail impostata per l'utente")
        else:
            data['email'] = email
            email_notify = user.email_notify
            user.email_notify = not email_notify
            data['notify_status'] = user.email_notify
            data['error'] = None
            user.save(update_fields=['email_notify'])
        d = {'data': data}
        return render(request, 'intercooler-notify.html', context=d)
    raise Http404

@login_required
@has_access_to_ticket
def ticket_detail_print(request, ticket_id, ticket):
    """
    Displays ticket print version

    :type ticket_id: String
    :type ticket: Ticket (from @has_access_to_ticket)

    :param ticket_id: ticket code
    :param ticket: ticket object (from @has_access_to_ticket)

    :return: view response
    """
    response = user.ticket_detail(request,
                                  ticket_id=ticket_id,
                                  template='ticket_detail_print.html')
    return response

@login_required
def user_settings(request, structure_slug=None,
                  structure=None, office_employee=None):
    """
    Gets user settings

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_manager/@is_operator)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param structure: structure object (from @is_manager/@is_operator)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: response
    """
    user_type = get_user_type(request.user, structure)
    template = "{}/user_settings.html".format(user_type)
    title = _("Configurazione impostazioni")
    sub_title = _("e riepilogo dati personali")
    d = {'structure': structure,
         'sub_title': sub_title,
         'title': title,}
    response = render(request, template, d)
    return response

@login_required
def ticket_messages(request, structure_slug=None,
                    structure=None, office_employee=None):
    """
    Gets ticket messages

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_manager/@is_operator)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param structure: structure object (from @is_manager/@is_operator)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: response
    """
    user_type = get_user_type(request.user, structure)
    by_operator = False
    if user_type=='user':
        tickets = Ticket.objects.filter(created_by=request.user)
        # if user_type is 'user', retrieve messages leaved by a manager/operator
        # (linked to a structure)
        by_operator = True
    elif user_type=='operator':
        # if user is an operator, retrieve his tickets
        user_tickets = visible_tickets_to_user(user=request.user,
                                               structure=structure,
                                               office_employee=office_employee)
        tickets = Ticket.objects.filter(code__in=user_tickets)
    else:
        # if user is a manager, get structure tickets
        ta = TicketAssignment
        structure_tickets = ta.get_ticket_per_structure(structure=structure)
        tickets = Ticket.objects.filter(code__in=structure_tickets)
    tickets_with_messages = []
    for ticket in tickets:
        messages = ticket.get_messages_count(by_operator=by_operator)
        # fill the messages list (of tuples)
        if messages[0] > 0:
            # Tuple with messages infos
            # ticket, all_ticket_messages, ticket_unread_messages, first_ticket_creation_date
            tm = (ticket, messages[0], messages[1], messages[2])
            tickets_with_messages.append(tm)
    tickets_with_messages.sort(key=lambda e: (e[2], e[3]), reverse=True)
    paginator = Paginator(tickets_with_messages, 10)
    page = request.GET.get('page')
    tickets_with_messages = paginator.get_page(page)
    template = "{}/ticket_messages.html".format(user_type)
    title = _("Tutti i messaggi")
    d = {'structure': structure,
         'tickets_with_messages': tickets_with_messages,
         'title': title,}
    response = render(request, template, d)
    return response

@login_required
def ticket_message_delete(request, ticket_message_id):
    """
    Deletes a message from ticket chat

    :type ticket_message_id: Integer

    :param ticket_message_id: ticket message id

    :return: redirect
    """
    ticket_message = get_object_or_404(TicketReply, pk=ticket_message_id)
    last_message = TicketReply.objects.filter(ticket=ticket_message.ticket).last()
    structure = ticket_message.structure
    # if message doesn't exist
    if not ticket_message:
        return custom_message(request, _("Impossibile recuperare il messaggio"),
                              structure_slug=structure.slug)
    # if user isn't the owner of message
    if ticket_message.owner!=request.user:
        return custom_message(request, _("Permesso negato"),
                              structure_slug=structure.slug)
    # if message has already been read
    if ticket_message.read_date:
        return custom_message(request, _("Impossibile eliminare il"
                                         " messaggio dopo che è stato letto"),
                              structure_slug=structure.slug)
    user_type = get_user_type(request.user, structure)
    # if message is not the last in chat
    if ticket_message != last_message:
        return custom_message(request, _("Impossibile eliminare il"
                                         " messaggio dopo che è stato letto"
                                         " da altri operatori"),
                              structure_slug=structure.slug)
    user_type = get_user_type(request.user, structure)
    # if message is from a manager/operator and user_type is 'user'
    if structure and user_type=='user':
        return custom_message(request, _("Permesso negato"),
                              structure_slug=structure.slug)
    ticket = ticket_message.ticket
    messages.add_message(request, messages.SUCCESS,
                         _("Messaggio <b>{}</b> eliminato con successo.".format(ticket_message)))
    # delete message attachment
    delete_file(file_name=ticket_message.attachment)
    # delete message
    ticket_message.delete()
    if user_type=='user':

        # Send mail to ticket owner
        mail_params = {'hostname': settings.HOSTNAME,
                       'status': _("eliminato"),
                       'ticket': ticket,
                       'user': request.user
                      }
        m_subject = _("{} - ticket {} messaggio eliminato".format(settings.HOSTNAME,
                                                                  ticket))
        send_custom_mail(subject=m_subject,
                         recipient=request.user,
                         body=USER_TICKET_MESSAGE,
                         params=mail_params)
        # END Send mail to ticket owner

        return redirect('uni_ticket:ticket_message',
                        ticket_id=ticket.code)
    return redirect('uni_ticket:manage_ticket_message_url',
                    structure_slug=structure.slug,
                    ticket_id=ticket.code)

@login_required
def download_condition_attachment(request, category_slug, condition_id):
    """
    Downloads ticket attachment

    :type ticket_id:String
    :type attachment: String
    :type ticket: Ticket (from @has_access_to_ticket)

    :param ticket_id: ticket code
    :param attachment: attachment name
    :param ticket: ticket object (from @has_access_to_ticket)

    :return: file
    """
    category = get_object_or_404(TicketCategory, slug=category_slug)
    condition = get_object_or_404(TicketCategoryCondition,
                                  category=category,
                                  pk=condition_id)
    attachment = condition.attachment
    if attachment:
        path = '{}/{}/{}/{}'.format(settings.MEDIA_ROOT,
                                    settings.HOSTNAME,
                                    CATEGORY_CONDITIONS_ATTACHMENT_SUBFOLDER,
                                    category.slug)
        # get file
        result = download_file(path, os.path.basename(condition.attachment.name))
        return result
    raise Http404
