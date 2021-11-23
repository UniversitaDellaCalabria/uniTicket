import os

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Min, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.translation import gettext as _

from django_form_builder.utils import get_as_dict
from organizational_area.models import OrganizationalStructure

from uni_ticket.decorators import *
from uni_ticket.models import *
from uni_ticket.settings import USER_TICKET_MESSAGE
from uni_ticket.utils import *


@login_required
def manage(request, structure_slug=None):
    """
    Makes URL redirect to manage a structure depending of user role

    :type structure_slug: String

    :param structure_slug: slug of structure to manage

    :return: redirect
    """
    if not structure_slug:
        return redirect("uni_ticket:user_dashboard")
    structure = get_object_or_404(OrganizationalStructure, slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    if user_type == "user":
        return redirect("uni_ticket:user_dashboard")
    return redirect(
        "uni_ticket:{}_dashboard".format(user_type), structure_slug=structure_slug
    )


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
    json_dict = ticket.get_modulo_compilato()
    ticket_details = get_as_dict(compiled_module_json=json_dict)
    if attachment:
        # get ticket attachments
        attachments = ticket_details[settings.ATTACHMENTS_DICT_PREFIX]
        # get the attachment
        documento = attachments[attachment]
        # get ticket folder path
        path_allegato = get_path(ticket.get_folder())
        # get file
        result = download_file(path_allegato, documento)
        return result
    raise Http404


@login_required
@has_access_to_ticket
def download_message_attachment(
    request, ticket_id, reply_id, ticket
):  # pragma: no cover
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
        path_allegato = get_path(message.get_folder())
        # get file
        result = download_file(
            path_allegato, os.path.basename(message.attachment.name))
        return result
    raise Http404


@login_required
def download_task_attachment(request, ticket_id, task_id):
    """
    Downloads ticket message attachment

    :type ticket_id: String
    :type task_id: String

    :param ticket_id: ticket code
    :param task_id: task code

    :return: file
    """
    # get ticket
    ticket = get_object_or_404(Ticket, code=ticket_id)
    # get task
    task = get_object_or_404(Task, code=task_id)

    # current user is ticket owner?
    is_owner = ticket.check_if_owner(request.user)

    # current user is a valid ticket operator?
    is_operator = False
    # Select all offices that follow the ticket (readonly too)
    offices = ticket.get_assigned_to_offices(ignore_follow=False)
    # Check if user is operator of the ticket office
    for office in offices:
        if user_manage_office(request.user, office):
            is_operator = True
            break

    if not is_owner and not is_operator:
        return custom_message(request, _("Accesso al ticket negato."))
    elif not task.is_public and not is_operator:
        return custom_message(request, _("Attività riservata agli operatori"))

    # if task has attachment
    if task.attachment:
        # get ticket task folder path
        path_allegato = get_path(task.get_folder())
        # get file
        result = download_file(
            path_allegato, os.path.basename(task.attachment.name))
        return result
    raise Http404


@login_required
def opened_ticket(request, structure_slug=None, structure=None, office_employee=None):
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
    title = _("Richieste assegnate")
    user_type = get_user_type(request.user, structure)
    template = "{}/opened_ticket.html".format(user_type)
    d = {
        "structure": structure,
        "sub_title": structure,
        "title": title,
    }
    return render(request, template, d)


@login_required
def my_opened_ticket(
    request, structure_slug=None, structure=None, office_employee=None
):
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
    title = _("Richieste assegnate a me")
    user_type = get_user_type(request.user, structure)
    template = "{}/my_opened_ticket.html".format(user_type)
    d = {
        "structure": structure,
        "sub_title": structure,
        "title": title,
    }
    return render(request, template, d)


@login_required
def unassigned_ticket(
    request, structure_slug=None, structure=None, office_employee=None
):
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
    title = _("Richieste aperte")
    user_type = get_user_type(request.user, structure)
    template = "{}/unassigned_ticket.html".format(user_type)
    d = {
        "structure": structure,
        "sub_title": structure,
        "title": title,
    }
    return render(request, template, d)


@login_required
def closed_ticket(request, structure_slug=None, structure=None, office_employee=None):
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
    title = _("Richieste chiuse")
    user_type = get_user_type(request.user, structure)
    template = "{}/closed_ticket.html".format(user_type)
    d = {
        "structure": structure,
        "sub_title": structure,
        "title": title,
    }
    return render(request, template, d)


@login_required
def email_notify_change(request):
    if request.method == "POST":
        data = {}
        user = request.user
        email = user.email
        if not email:
            data["error"] = _("Nessuna e-mail impostata per l'utente")
        else:
            data["email"] = email
            email_notify = user.email_notify
            user.email_notify = not email_notify
            data["notify_status"] = user.email_notify
            data["error"] = None
            user.save(update_fields=["email_notify"])
        d = {"data": data}
        return render(request, "intercooler-notify.html", context=d)
    raise Http404


@login_required
def user_settings(
    request, structure_slug=None, structure=None, office_employee=None
):  # pragma: no cover
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
    d = {
        "structure": structure,
        "sub_title": sub_title,
        "title": title,
    }
    response = render(request, template, d)
    return response


@login_required
def ticket_messages(request, structure_slug=None, structure=None, office_employee=None):
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
    if user_type == "user":
        tickets = Ticket.objects.filter(
            Q(created_by=request.user) | Q(compiled_by=request.user)
        ).values("code")
        # if user_type is 'user', retrieve messages leaved by a manager/operator
        # (linked to a structure)
        by_operator = True
    elif user_type == "operator":
        # if user is an operator, retrieve his tickets
        tickets = visible_tickets_to_user(
            user=request.user, structure=structure, office_employee=office_employee
        )
    else:
        # if user is a manager, get structure tickets
        ta = TicketAssignment
        tickets = ta.get_ticket_per_structure(structure=structure)

    if by_operator:
        not_read = Count(
            "id", filter=Q(read_date__isnull=True, structure__isnull=False)
        )
    else:
        not_read = Count("id", filter=Q(
            read_date__isnull=True, structure__isnull=True))

    started = Min("created")
    ticket_messages = (
        TicketReply.objects.filter(ticket__code__in=tickets)
        .values(
            "ticket__code",
            "ticket__subject",
            "ticket__input_module__ticket_category__name",
            "ticket__created_by__first_name",
            "ticket__created_by__last_name",
        )
        .annotate(total=Count("id"))
        .annotate(not_read=not_read)
        .annotate(started=started)
        .order_by("-not_read", "-started")
    )
    paginator = Paginator(ticket_messages, 10)
    page = request.GET.get("page")
    ticket_messages = paginator.get_page(page)
    template = "{}/ticket_messages.html".format(user_type)
    title = _("Tutti i messaggi")
    d = {
        "structure": structure,
        "ticket_messages": ticket_messages,
        "title": title,
    }
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
    last_message = TicketReply.objects.filter(
        ticket=ticket_message.ticket).last()
    structure = ticket_message.structure
    # if message doesn't exist
    if not ticket_message:
        return custom_message(
            request,
            _("Impossibile recuperare il messaggio"),
            structure_slug=structure.slug if structure else "",
        )
    # if user isn't the owner of message
    if ticket_message.owner != request.user:
        return custom_message(
            request,
            _("Permesso negato"),
            structure_slug=structure.slug if structure else "",
        )
    # if message has already been read
    if ticket_message.read_date:
        return custom_message(
            request,
            _("Impossibile eliminare il" " messaggio dopo che è stato letto"),
            structure_slug=structure.slug if structure else "",
        )
    user_type = get_user_type(request.user, structure)
    # if message is not the last in chat
    # if ticket_message != last_message:
    # return custom_message(request, _("Impossibile eliminare il"
    # " messaggio dopo che è stato letto"
    # " da altri operatori"),
    # structure_slug=structure.slug)
    user_type = get_user_type(request.user, structure)
    # if message is from a manager/operator and user_type is 'user'
    if structure and user_type == "user":
        return custom_message(
            request, _("Permesso negato"), structure_slug=structure.slug
        )
    ticket = ticket_message.ticket
    messages.add_message(
        request,
        messages.SUCCESS,
        _("Messaggio <b>{}</b> eliminato con successo." "").format(ticket_message),
    )

    # delete message
    msg_subject = ticket_message.subject
    msg_text = ticket_message.text

    ticket_message.delete()

    # add to ticket log history
    log_msg = _("Messaggio eliminato. Oggetto: {}" "").format(msg_subject)
    ticket.update_log(request.user, note=log_msg, send_mail=False)

    if user_type == "user":

        # Send mail to ticket owner
        mail_params = {
            "hostname": settings.HOSTNAME,
            "status": _("eliminato"),
            "message_subject": msg_subject,
            "message_text": msg_text,
            "ticket": ticket,
            "user": request.user,
            "url": request.build_absolute_uri(
                reverse("uni_ticket:ticket_message",
                        kwargs={"ticket_id": ticket.code})
            ),
        }
        m_subject = _("{} - richiesta {} messaggio eliminato" "").format(
            settings.HOSTNAME, ticket
        )
        send_custom_mail(
            subject=m_subject,
            recipients=[request.user],
            body=USER_TICKET_MESSAGE,
            params=mail_params,
        )
        # END Send mail to ticket owner

        return redirect("uni_ticket:ticket_message", ticket_id=ticket.code)
    return redirect(
        "uni_ticket:manage_ticket_message_url",
        structure_slug=structure.slug,
        ticket_id=ticket.code,
    )


@login_required
def download_condition_attachment(request, structure_slug, category_slug, condition_id):
    """
    Downloads ticket attachment

    :type structure_slug:String
    :type category_slug:String
    :type condition_id: Integer

    :param structure_slug: Organizational Structure slug
    :param category_slug: Ticket Category slug
    :param condition_id: Condition pk

    :return: file
    """
    category = get_object_or_404(
        TicketCategory,
        slug=category_slug,
        is_active=True,
        organizational_structure__slug=structure_slug,
        organizational_structure__is_active=True,
    )
    condition = get_object_or_404(
        TicketCategoryCondition, category=category, pk=condition_id
    )
    if condition.attachment:
        # get ticket folder path
        path_allegato = get_path(condition.get_folder())
        # get file
        result = download_file(
            path_allegato, os.path.basename(condition.attachment.name)
        )
        return result
    raise Http404
