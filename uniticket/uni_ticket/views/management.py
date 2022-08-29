import logging
import os
import zipfile

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import LogEntry
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils.html import strip_tags
from django.utils.translation import gettext as _

from django_form_builder.utils import get_as_dict, get_labeled_errors
from organizational_area.models import *
from uni_ticket.decorators import (
    has_ticket_admin_privileges,
    ticket_assigned_to_structure,
    ticket_is_taken_and_not_closed,
    ticket_is_taken_for_employee,
)
from uni_ticket.forms import *
from uni_ticket.models import *
from uni_ticket.settings import (
    NEW_TICKET_ASSIGNED_TO_OPERATOR_BODY,
    READONLY_COMPETENCE_OVER_TICKET,
    SIMPLE_USER_SHOW_PRIORITY,
    STATS_DEFAULT_DATE_START_DELTA_DAYS,
    USER_TICKET_MESSAGE,
    JS_CHART_CDN_URL,
    STATS_TIME_SLOTS,
    STATS_MAX_DAYS,
    STATS_HEAT_MAP_RANGES
)
from uni_ticket.utils import *
from uni_ticket.statistics import uniTicketStats


logger = logging.getLogger(__name__)


@login_required
def manage_opened_ticket_url(request, structure_slug):  # pragma: no cover
    """
    Makes URL redirect to opened ticket page depending of user role

    :type structure_slug: String

    :param structure_slug: slug of structure to manage

    :return: redirect
    """
    structure = get_object_or_404(OrganizationalStructure, slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect("uni_ticket:{}_opened_ticket".format(user_type), structure_slug)


@login_required
def manage_unassigned_ticket_url(request, structure_slug):  # pragma: no cover
    """
    Makes URL redirect to unassigned ticket page depending of user role

    :type structure_slug: String

    :param structure_slug: slug of structure to manage

    :return: redirect
    """
    structure = get_object_or_404(OrganizationalStructure, slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect("uni_ticket:{}_unassigned_ticket".format(user_type), structure_slug)


@login_required
def manage_closed_ticket_url(request, structure_slug):  # pragma: no cover
    """
    Makes URL redirect to closed ticket page depending of user role

    :type structure_slug: String

    :param structure_slug: slug of structure to manage

    :return: redirect
    """
    structure = get_object_or_404(OrganizationalStructure, slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect("uni_ticket:{}_closed_ticket".format(user_type), structure_slug)


@login_required
def manage_not_closed_ticket_url(request, structure_slug):  # pragma: no cover
    """
    Makes URL redirect to not closed ticket page depending of user role

    :type structure_slug: String

    :param structure_slug: slug of structure to manage

    :return: redirect
    """
    structure = get_object_or_404(OrganizationalStructure, slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect("uni_ticket:{}_not_closed_ticket".format(user_type), structure_slug)


@login_required
def manage_ticket_url(request, structure_slug):  # pragma: no cover
    """
    Builds a fake URL to ticket detail page for datatables <href> tags

    :type structure_slug: String

    :param structure_slug: slug of structure to manage

    :return: render
    """
    return custom_message(request, _("Permesso negato"), structure_slug)


@login_required
@has_ticket_admin_privileges
@ticket_assigned_to_structure
def manage_ticket_url_detail(
    request, structure_slug, ticket_id, structure, can_manage, ticket
):  # pragma: no cover
    """
    Redirects URL ticket detail page depending of user role

    :type structure_slug: String
    :type ticket_id: String
    :type structure: OrganizationalStructure (from @has_ticket_admin_privileges)
    :type can_manage: Dictionary (from @has_ticket_admin_privileges)
    :type ticket: Ticket(from @ticket_assigned_to_structure)

    :param structure_slug: slug of structure to manage
    :param ticket_id: code of ticket
    :param structure: structure object (from @has_ticket_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_ticket_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)

    :return: redirect
    """
    request.user
    user_type = get_user_type(request.user, structure)
    return redirect(
        "uni_ticket:{}_manage_ticket".format(user_type),
        structure_slug=structure_slug,
        ticket_id=ticket_id,
    )


@login_required
@has_ticket_admin_privileges
@ticket_assigned_to_structure
def ticket_detail(
    request,
    structure_slug,
    ticket_id,
    structure,
    can_manage,
    ticket,
    office_employee=None,
):
    """
    Ticket detail management page

    :type structure_slug: String
    :type ticket_id: String
    :type structure: OrganizationalStructure (from @has_ticket_admin_privileges)
    :type can_manage: Dictionary (from @has_ticket_admin_privileges)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)
    :type ticket: Ticket (from @ticket_assigned_to_structure)

    :param structure_slug: slug of structure to manage
    :param ticket_id: code
    :param structure: OrganizationalStructure (from @has_ticket_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_ticket_admin_privileges)
    :param office_employee: operator offices queryset (from @is_operator)
    :param ticket: Ticket (from @ticket_assigned_to_structure)

    :return: render
    """
    title = ticket.subject
    sub_title = ticket.code
    user = request.user
    user_type = get_user_type(request.user, structure)
    json_dict = ticket.get_modulo_compilato()
    ticket_details = get_as_dict(
        compiled_module_json=json_dict, allegati=False, formset_management=False
    )
    priority = ticket.get_priority()
    allegati = ticket.get_allegati_dict()
    path_allegati = get_path(ticket.get_folder())
    ticket_form = ticket.input_module.get_form(
        files=allegati, remove_filefields=False)
    ticket_logs = LogEntry.objects.filter(
        content_type_id=ContentType.objects.get_for_model(ticket).pk,
        object_id=ticket.pk,
    )
    ticket_task = Task.objects.filter(ticket=ticket)
    ticket_dependences = ticket.get_dependences()
    ticket_assignments = TicketAssignment.objects.filter(ticket=ticket)

    # priority form
    form = PriorityForm(initial={"priorita": ticket.priority})

    # offices that have to take ticket
    untaken_user_offices = ticket.is_untaken_by_user_offices(
        user=request.user, structure=structure
    )
    offices_forms = {}
    for u_office in untaken_user_offices:
        if user_manage_office(user, u_office):
            # take ticket form
            office_priority_form = TakeTicketForm(
                initial={"priority": ticket.priority}, office_referred=u_office
            )
            # assign ticket form
            office_operators_form = AssignTicketToOperatorForm(
                initial={"priorita": ticket.priority},
                structure=structure,
                office=u_office,
                current_user=user,
            )
            # assign forms to every untaken office
            offices_forms[u_office] = (
                office_priority_form, office_operators_form)

    if request.method == "POST":
        if can_manage["readonly"]:
            messages.add_message(
                request, messages.ERROR, READONLY_COMPETENCE_OVER_TICKET
            )
            return redirect(
                "uni_ticket:manage_ticket_url_detail",
                structure_slug=structure_slug,
                ticket_id=ticket_id,
            )
        if ticket.is_closed:
            messages.add_message(
                request, messages.ERROR, _(
                    "Impossibile modificare un ticket chiuso")
            )
            return redirect(
                "uni_ticket:manage_ticket_url_detail",
                structure_slug=structure_slug,
                ticket_id=ticket_id,
            )

        # check if user has taken or assigned competence
        for o in offices_forms:
            office_priority_form = TakeTicketForm(
                request.POST, office_referred=o)
            office_op_form = AssignTicketToOperatorForm(
                request.POST,
                structure=o.organizational_structure,
                office=o,
                current_user=user,
            )
            assignment = TicketAssignment.objects.filter(
                ticket=ticket, office=o, follow=True, taken_date__isnull=True
            ).first()
            # if user has taken ticket
            if office_priority_form.is_valid() and assignment:
                assignment.taken_date = timezone.localtime()
                assignment.taken_by = request.user
                assignment.save(update_fields=["taken_date", "taken_by"])
                priority = office_priority_form.cleaned_data["priority"]
                ticket.priority = priority
                ticket.save(update_fields=["priority"])
                priority_text = dict(PRIORITY_LEVELS).get(priority)
                msg = _(
                    "Ticket preso in carico da {}. "
                    "Priorità assegnata: {}".format(
                        request.user, priority_text)
                )
                if not SIMPLE_USER_SHOW_PRIORITY:
                    msg = _("Ticket preso in carico da {}.".format(request.user))
                ticket.update_log(user=request.user, note=msg)
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    _(
                        "Ticket <b>{}</b> assegnato"
                        " con successo a {}".format(ticket.code, request.user)
                    ),
                )
                return redirect(
                    "uni_ticket:manage_ticket_url_detail",
                    structure_slug=structure_slug,
                    ticket_id=ticket_id,
                )
            # if manager has assigned ticket to office operator
            elif office_op_form.is_valid() and assignment:
                operator = office_op_form.cleaned_data["assign_to"]
                priority = office_op_form.cleaned_data["priorita"]
                ticket.priority = priority
                ticket.save(update_fields=["priority"])
                assignment.taken_date = timezone.localtime()
                assignment.taken_by = operator
                assignment.assigned_by = request.user
                assignment.save(
                    update_fields=["assigned_by",
                                   "taken_date", "taken_by", "modified"]
                )
                priority_text = dict(PRIORITY_LEVELS).get(priority)
                msg = _(
                    "Richiesta assegnata a {} da {}. "
                    "Priorità assegnata: {}".format(
                        operator, request.user, priority_text
                    )
                )
                if not SIMPLE_USER_SHOW_PRIORITY:
                    msg = _(
                        "Richiesta assegnata a {} da {}.".format(
                            operator, request.user)
                    )
                ticket.update_log(user=request.user, note=msg)
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    _(
                        "Richiesta <b>{}</b> assegnata"
                        " con successo a {}".format(ticket.code, operator)
                    ),
                )

                # Send mail to operator
                mail_params = {
                    "hostname": settings.HOSTNAME,
                    "user": operator,
                    "manager": request.user,
                    "ticket_user": ticket.created_by,
                    "ticket_subject": ticket.subject,
                    "ticket_description": ticket.description,
                    "ticket_url": request.build_absolute_uri(
                        reverse(
                            "uni_ticket:manage_ticket_url_detail",
                            kwargs={
                                "structure_slug": structure.slug,
                                "ticket_id": ticket.code,
                            },
                        )
                    ),
                }
                m_subject = _(
                    "{} - richiesta {} assegnata".format(
                        settings.HOSTNAME, ticket)
                )
                send_custom_mail(
                    subject=m_subject,
                    recipients=[operator],
                    body=NEW_TICKET_ASSIGNED_TO_OPERATOR_BODY,
                    params=mail_params,
                )

                return redirect(
                    "uni_ticket:manage_ticket_url_detail",
                    structure_slug=structure_slug,
                    ticket_id=ticket_id,
                )

        # operator/manager has changed priority
        form = PriorityForm(request.POST)
        if (
            ticket.has_been_taken(structure=structure, exclude_readonly=True)
            and form.is_valid()
        ):
            priority = form.cleaned_data["priorita"]
            priority_text = dict(PRIORITY_LEVELS).get(priority)
            mail_params = {
                "hostname": settings.HOSTNAME,
                "status": _("aggiornato"),
                "ticket": ticket,
                "user": ticket.created_by,
            }

            msg = _("Priorità aggiornata")
            if SIMPLE_USER_SHOW_PRIORITY:
                msg = _("Priorità assegnata: {}".format(priority_text))

            ticket.update_log(user=request.user, note=msg)
            ticket.priority = priority
            ticket.save(update_fields=["priority"])
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Richiesta <b>{}</b> aggiornata" " con successo").format(ticket.code),
            )
            return redirect(
                "uni_ticket:manage_ticket_url_detail",
                structure_slug=structure_slug,
                ticket_id=ticket_id,
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )

    d = {
        "allegati": allegati,
        "dependences": ticket_dependences,
        "details": ticket_details,
        "form": form,
        "offices_forms": offices_forms,
        "path_allegati": path_allegati,
        "priority": priority,
        "structure": structure,
        "sub_title": sub_title,
        "ticket": ticket,
        "ticket_assignments": ticket_assignments,
        "ticket_form": ticket_form,
        "logs": ticket_logs,
        "ticket_task": ticket_task,
        "title": title,
        "untaken_user_offices": untaken_user_offices,
    }
    template = "{}/ticket_detail.html".format(user_type)
    return render(request, template, d)


@login_required
def tickets(request, structure_slug, structure, office_employee=None):
    """
    All tickets to manage

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_manager/@is_operator)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: the slug of structure to manage
    :param structure: structure object (from @is_manager/@is_operator)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    user_type = get_user_type(request.user, structure)
    template = "{}/tickets.html".format(user_type)
    title = _("Gestione richieste")
    sub_title = _("Tutti gli stati")

    ticket_list = []
    # if user is operator
    if office_employee:
        ticket_list = visible_tickets_to_user(
            user=request.user, structure=structure, office_employee=office_employee
        )
    # if user is manager
    else:
        ticket_list = TicketAssignment.get_ticket_per_structure(structure)

    tickets = Ticket.objects.filter(code__in=ticket_list)

    not_closed = tickets.filter(is_closed=False)
    # unassigned = []
    # opened = []
    # my_opened = []
    unassigned = 0
    opened = 0
    my_opened = 0
    for nc in not_closed:
        if nc.has_been_taken():
            # opened.append(nc)
            opened += 1
            if nc.has_been_taken_by_user(structure=structure, user=request.user):
                # my_opened.append(nc)
                my_opened += 1
        else:
            # unassigned.append(nc)
            unassigned += 1
    # chiusi = Ticket.objects.filter(code__in=ticket_list, is_closed=True)
    chiusi = tickets.filter(is_closed=True).count()

    # unread messages
    messages = TicketReply.get_unread_messages_count(tickets=tickets)

    d = {
        "ticket_aperti": opened,
        "ticket_assegnati_a_me": my_opened,
        "ticket_chiusi": chiusi,
        "ticket_non_gestiti": unassigned,
        "ticket_messages": messages,
        "structure": structure,
        "sub_title": sub_title,
        "title": title,
    }
    return render(request, template, d)


@login_required
def ticket_dependence_add_url(request, structure_slug, ticket_id):
    """
    Makes URL redirect to add ticket dependence by user role

    :type structure_slug: String
    :type ticket_id: String

    :param structure_slug: structure slug
    :param ticket_id: ticket code

    :return: redirect
    """
    structure = get_object_or_404(OrganizationalStructure, slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect(
        "uni_ticket:{}_add_ticket_dependence".format(user_type),
        structure_slug,
        ticket_id,
    )


@login_required
@has_ticket_admin_privileges
@ticket_is_taken_for_employee
@ticket_assigned_to_structure
@ticket_is_taken_and_not_closed
def ticket_dependence_add_new(
    request,
    structure_slug,
    ticket_id,
    structure,
    can_manage,
    ticket,
    office_employee=None,
):
    """
    Adds ticket dependence

    :type structure_slug: String
    :type ticket_id: String
    :type structure: OrganizationalStructure (from @has_ticket_admin_privileges)
    :type can_manage: Dictionary (from @has_ticket_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param structure: structure object (from @has_ticket_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_ticket_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    user_type = get_user_type(request.user, structure)
    template = "{}/add_ticket_dependence.html".format(user_type)
    title = _("Aggiungi dipendenza da richiesta")
    sub_title = "{} ({})".format(ticket.subject, ticket_id)
    # Lista dei pk dei ticket da cui quello corrente dipende
    ticket_dependences = ticket.get_dependences()
    ticket_dependences_code_list = []
    for td in ticket_dependences:
        if td.main_ticket.code not in ticket_dependences_code_list:
            ticket_dependences_code_list.append(td.main_ticket.code)
    form = TicketDependenceForm(
        user=request.user,
        structure=structure,
        ticket_id=ticket.code,
        ticket_dependences=ticket_dependences_code_list,
    )
    if request.method == "POST":
        form = TicketDependenceForm(
            request.POST,
            user=request.user,
            structure=structure,
            ticket_id=ticket.code,
            ticket_dependences=ticket_dependences_code_list,
        )
        if form.is_valid():
            main_ticket = form.cleaned_data["ticket"]
            note = form.cleaned_data["note"]
            if Ticket2Ticket.main_is_already_used(main_ticket):
                messages.add_message(
                    request,
                    messages.ERROR,
                    _(
                        "La dipendenza non può essere aggiunta. "
                        "La richiesta <b>{}</b> è dipendente da "
                        "altre richieste"
                    ).format(main_ticket),
                )
                return redirect(
                    "uni_ticket:add_ticket_dependence_url",
                    structure_slug=structure_slug,
                    ticket_id=ticket_id,
                )
            if ticket.blocks_some_ticket():
                messages.add_message(
                    request,
                    messages.ERROR,
                    _(
                        "La dipendenza non può essere aggiunta. "
                        "Ci sono richieste che dipendono da "
                        "quella corrente <b>{}</b>"
                    ).format(ticket),
                )
                return redirect(
                    "uni_ticket:add_ticket_dependence_url",
                    structure_slug=structure_slug,
                    ticket_id=ticket_id,
                )
            t2t = Ticket2Ticket(
                subordinate_ticket=ticket, main_ticket=main_ticket, note=note
            )
            t2t.save()

            # log action
            logger.info(
                "[{}] {} added new dependence to"
                " ticket {} from ticket {}".format(
                    timezone.localtime(), request.user, ticket, main_ticket
                )
            )

            ticket.update_log(
                user=request.user,
                note=_(
                    "Aggiunta dipendenza dalla richiesta:" " {}".format(
                        main_ticket)
                ),
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                _(
                    "Dipendenza dalla richiesta <b>{}</b>" " aggiunta con successo"
                ).format(main_ticket.code),
            )
            return redirect(
                "uni_ticket:manage_ticket_url_detail",
                structure_slug=structure_slug,
                ticket_id=ticket_id,
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )
    d = {
        "form": form,
        "structure": structure,
        "sub_title": sub_title,
        "ticket": ticket,
        "title": title,
    }
    return render(request, template, d)


@login_required
@has_ticket_admin_privileges
@ticket_is_taken_for_employee
@ticket_assigned_to_structure
@ticket_is_taken_and_not_closed
def ticket_dependence_remove(
    request, structure_slug, ticket_id, main_ticket_id, structure, can_manage, ticket
):
    """
    Removes ticket dependence

    :type structure_slug: String
    :type ticket_id: String
    :type main_ticket_id: String
    :type structure: OrganizationalStructure (from @has_ticket_admin_privileges)
    :type can_manage: Dictionary (from @has_ticket_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param main_ticket_id: main ticket code
    :param structure: structure object (from @has_ticket_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_ticket_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)

    :return: redirect
    """
    get_user_type(request.user, structure)
    main_ticket = get_object_or_404(Ticket, code=main_ticket_id)
    to_remove = get_object_or_404(
        Ticket2Ticket, subordinate_ticket=ticket, main_ticket=main_ticket
    )
    # Se il ticket main che sto eliminando non è assegnato alla struttura corrente
    if structure not in main_ticket.get_assigned_to_structures():
        return custom_message(
            request,
            _(
                "La richiesta <b>{}</b> non è stata assegnata"
                " a questa struttura, pertanto"
                " non puoi gestirla"
            ).format(main_ticket),
            structure_slug=structure.slug,
        )
    else:
        # log action
        logger.info(
            "[{}] {} removed dependence to"
            " ticket {} from ticket {}".format(
                timezone.localtime(), request.user, ticket, main_ticket
            )
        )
        to_remove.delete()
        ticket.update_log(
            user=request.user,
            note=_("Rimossa dipendenza dalla richiesta:" " {}".format(main_ticket)),
        )
        messages.add_message(
            request, messages.SUCCESS, _("Dipendenza rimossa correttamente")
        )
    return redirect(
        "uni_ticket:manage_ticket_url_detail",
        structure_slug=structure_slug,
        ticket_id=ticket_id,
    )


@login_required
def ticket_close_url(request, structure_slug, ticket_id):  # pragma: no cover
    """
    Makes URL redirect to closing ticket page depending of user role

    :type structure_slug: String
    :type ticket_id: String

    :param structure_slug: structure slug
    :param ticket_id: ticket code

    :render: redirect
    """
    structure = get_object_or_404(OrganizationalStructure, slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect(
        "uni_ticket:{}_close_ticket".format(
            user_type), structure_slug, ticket_id
    )


@login_required
@has_ticket_admin_privileges
@ticket_is_taken_for_employee
@ticket_assigned_to_structure
@ticket_is_taken_and_not_closed
def ticket_close(
    request,
    structure_slug,
    ticket_id,
    structure,
    can_manage,
    ticket,
    office_employee=None,
):
    """
    Closes ticket

    :type structure_slug: String
    :type ticket_id: String
    :type structure: OrganizationalStructure (from @has_ticket_admin_privileges)
    :type can_manage: Dictionary (from @has_ticket_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param structure: structure object (from @has_ticket_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_ticket_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    # Se il ticket non è chiudibile (per dipendenze attive)
    if not ticket.is_closable():
        # log action
        logger.error(
            "[{}] {} tried to"
            " close not closable ticket {}".format(
                timezone.localtime(), request.user, ticket
            )
        )
        return custom_message(
            request,
            _("Non è possibile chiudere la richiesta," " ci sono dipendenze attive!"),
            structure_slug=structure.slug,
        )
    title = _("Chiusura della richiesta")
    sub_title = ticket

    category = ticket.input_module.ticket_category
    default_replies = TicketCategoryDefaultReply.objects.filter(
        ticket_category=category, is_active=True
    )

    form = TicketCloseForm()
    if request.method == "POST":
        form = TicketCloseForm(request.POST)
        if form.is_valid():
            motivazione = form.cleaned_data["note"]
            closing_status = form.cleaned_data["status"]
            ticket.is_closed = True
            ticket.closed_by = request.user
            ticket.closing_reason = motivazione.format(user=ticket.created_by)
            ticket.closing_status = closing_status
            ticket.closed_date = timezone.localtime()
            ticket.save(
                update_fields=[
                    "is_closed",
                    "closed_by",
                    "closing_reason",
                    "closing_status",
                    "closed_date",
                ]
            )

            # log action
            logger.info(
                "[{}] {} closed ticket {}".format(
                    timezone.localtime(), request.user, ticket
                )
            )

            ticket.update_log(
                user=request.user,
                note=_("Chiusura richiesta ({}): {}" "").format(
                    dict(CLOSING_LEVELS).get(closing_status), motivazione
                ),
            )

            opened_ticket_url = reverse(
                "uni_ticket:manage_opened_ticket_url",
                kwargs={"structure_slug": structure.slug},
            )

            messages.add_message(
                request,
                messages.SUCCESS,
                _(
                    "Richiesta {} chiusa correttamente"
                    "<br>"
                    "<a class='text-success' href='{}'><b>"
                    "Clicca qui per tornare alle richieste assegnate"
                    "</b></a>"
                ).format(ticket, opened_ticket_url),
            )
            return redirect(
                "uni_ticket:manage_ticket_url_detail",
                structure_slug=structure_slug,
                ticket_id=ticket_id,
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )

    user_type = get_user_type(request.user, structure)
    template = "{}/ticket_close.html".format(user_type)
    d = {
        "default_replies": default_replies,
        "form": form,
        "structure": structure,
        "sub_title": sub_title,
        "ticket": ticket,
        "title": title,
    }
    return render(request, template, d)


@login_required
@has_ticket_admin_privileges
@ticket_is_taken_for_employee
@ticket_assigned_to_structure
def ticket_reopen(request, structure_slug, ticket_id, structure, can_manage, ticket):
    """
    Reopen ticket

    :type structure_slug: String
    :type ticket_id: String
    :type structure: OrganizationalStructure (from @has_ticket_admin_privileges)
    :type can_manage: Dictionary (from @has_ticket_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param structure: structure object (from @has_ticket_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_ticket_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)

    :return: redirect
    """
    if not ticket.is_closed:
        # log action
        logger.error(
            "[{}] {} tried to reopen"
            " not closed ticket {}".format(
                timezone.localtime(), request.user, ticket)
        )
        return custom_message(
            request,
            _("La richiesta {} non è stata chiusa").format(ticket),
            structure_slug=structure.slug,
        )

    if ticket.is_notification:
        # log action
        logger.error(
            "[{}] {} tried to reopen"
            " a notification ticket {}".format(
                timezone.localtime(), request.user, ticket
            )
        )
        return custom_message(
            request,
            _("La richiesta {} non può essere riaperta").format(ticket),
            structure_slug=structure.slug,
        )

    if not ticket.closed_by:
        # log action
        logger.error(
            "[{}] {} tried to reopen"
            " a ticket closed by owner user{}"
            "".format(timezone.localtime(), request.user, ticket)
        )
        return custom_message(
            request,
            _(
                "La richiesta {} è stata chiusa dall'utente, "
                " pertanto non può essere riaperta"
            ).format(ticket),
            structure_slug=structure.slug,
        )

    # at least one of ticket offices must be active and must follow
    active_assignments = TicketAssignment.objects.filter(
        ticket=ticket, office__is_active=True, follow=True, readonly=False
    )
    if not active_assignments:
        return custom_message(
            request,
            _(
                "Nessuno degli uffici assegnati in precedenza "
                "può prendere nuovamente in carico la richiesta {} e "
                "pertanto questa non può essere riaperta"
            ).format(ticket),
            structure_slug=structure.slug,
        )
    ticket.is_closed = False
    ticket.save(update_fields=["is_closed"])
    ticket.update_log(user=request.user, note=_("Riapertura richiesta"))

    # log action
    logger.info(
        "[{}] {} reopened ticket {}".format(
            timezone.localtime(), request.user, ticket)
    )

    messages.add_message(
        request,
        messages.SUCCESS,
        _("Richiesta {} riaperta correttamente").format(ticket),
    )
    return redirect(
        "uni_ticket:manage_ticket_url_detail",
        structure_slug=structure_slug,
        ticket_id=ticket_id,
    )


@login_required
def ticket_competence_add_url(request, structure_slug, ticket_id):  # pragma: no cover
    """
    Makes URL redirect to adding ticket competence page depending of user role

    :type structure_slug: String
    :type ticket_id: String

    :param structure_slug: structure slug
    :param ticket_id: ticket code

    :return: redirect
    """
    structure = get_object_or_404(OrganizationalStructure, slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect(
        "uni_ticket:{}_add_ticket_competence".format(user_type),
        structure_slug,
        ticket_id,
    )


@login_required
@has_ticket_admin_privileges
@ticket_is_taken_for_employee
@ticket_assigned_to_structure
@ticket_is_taken_and_not_closed
def ticket_competence_add_new(
    request,
    structure_slug,
    ticket_id,
    structure,
    can_manage,
    ticket,
    office_employee=None,
):
    """
    Adds new ticket competence (first step)

    :type structure_slug: String
    :type ticket_id: String
    :type structure: OrganizationalStructure (from @has_ticket_admin_privileges)
    :type can_manage: Dictionary (from @has_ticket_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param structure: structure object (from @has_ticket_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_ticket_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    if can_manage["readonly"]:
        messages.add_message(request, messages.ERROR,
                             READONLY_COMPETENCE_OVER_TICKET)
        return redirect(
            "uni_ticket:manage_ticket_url_detail",
            structure_slug=structure_slug,
            ticket_id=ticket_id,
        )

    user_type = get_user_type(request.user, structure)
    template = "{}/add_ticket_competence.html".format(user_type)
    title = _("Trasferisci competenza richiesta")
    sub_title = "{} ({})".format(ticket.subject, ticket_id)
    strutture = OrganizationalStructure.objects.filter(is_active=True)
    d = {
        "structure": structure,
        "strutture": strutture,
        "sub_title": sub_title,
        "ticket": ticket,
        "title": title,
    }
    return render(request, template, d)


@login_required
@has_ticket_admin_privileges
@ticket_is_taken_for_employee
@ticket_assigned_to_structure
@ticket_is_taken_and_not_closed
def ticket_competence_add_final(
    request,
    structure_slug,
    ticket_id,
    new_structure_slug,
    structure,
    can_manage,
    ticket,
    office_employee=None,
):
    """
    Adds new ticket competence (second step)

    :type structure_slug: String
    :type ticket_id: String
    :type new_structure_slug: String
    :type structure: OrganizationalStructure (from @has_ticket_admin_privileges)
    :type can_manage: Dictionary (from @has_ticket_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param new_structure_slug: selected structure slug
    :param structure: structure object (from @has_ticket_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_ticket_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    strutture = OrganizationalStructure.objects.filter(is_active=True)
    # Lista uffici ai quali il ticket è assegnato
    ticket_offices = ticket.get_assigned_to_offices(office_active=False)

    operator_offices_list = []
    assignments = TicketAssignment.objects.filter(
        ticket=ticket,
        office__organizational_structure=structure,
        office__is_active=True,
        follow=True,
        taken_date__isnull=False,
    )
    for assignment in assignments:
        if user_manage_office(user=request.user, office=assignment.office):
            operator_offices_list.append(assignment.office)

    new_structure = get_object_or_404(
        OrganizationalStructure, slug=new_structure_slug, is_active=True
    )
    offices = OrganizationalStructureOffice.objects.filter(
        organizational_structure=new_structure, is_active=True
    )

    # exclude private offices if not in same structure
    if new_structure != structure:
        offices = offices.exclude(is_private=True)

    if request.method == "POST":
        form = TicketCompetenceSchemeForm(data=request.POST)
        if form.is_valid():
            office_slug = form.cleaned_data["office_slug"]
            follow = form.cleaned_data["follow"]
            readonly = form.cleaned_data["readonly"]
            selected_office_slug = form.cleaned_data["selected_office"]

            # L'ufficio passato in POST esiste?
            new_office = get_object_or_404(
                OrganizationalStructureOffice,
                slug=office_slug,
                organizational_structure=new_structure,
                is_active=True,
            )

            # se viene forzato il POST con un ufficio privato!
            if new_structure != structure and new_office.is_private:
                return custom_message(
                    request,
                    _("Impossibile assegnare la richiesta " "all'ufficio selezionato"),
                    structure_slug=structure.slug,
                )

            selected_office = None
            if selected_office_slug:
                selected_office = get_object_or_404(
                    OrganizationalStructureOffice,
                    slug=selected_office_slug,
                    organizational_structure=structure,
                    is_active=True,
                )

            if new_office in ticket_offices:
                messages.add_message(
                    request,
                    messages.ERROR,
                    _(
                        "La richiesta è già di competenza" " dell'ufficio <b>{}</b>" ""
                    ).format(new_office),
                )
                return redirect(
                    "uni_ticket:manage_ticket_url_detail",
                    structure_slug=structure_slug,
                    ticket_id=ticket_id,
                )

            messages.add_message(
                request,
                messages.SUCCESS,
                _("Competenza <b>{}</b> aggiunta" " correttamente".format(new_office)),
            )

            # If not follow anymore
            if not follow:
                abandoned_offices = ticket.block_competence(
                    user=request.user,
                    structure=structure,
                    allow_readonly=False,
                    selected_office=selected_office,
                )
                for off in abandoned_offices:
                    # if off.is_default:
                    # messages.add_message(request, messages.WARNING,
                    # _("L'ufficio <b>{}</b> non può essere"
                    # " rimosso dagli uffici competenti".format(off)))
                    # else:
                    ticket.update_log(
                        user=request.user,
                        note=_(
                            "Competenza abbandonata da" " Ufficio: {}".format(off)),
                    )

            # If follow but readonly
            elif readonly:
                abandoned_offices = ticket.block_competence(
                    user=request.user,
                    structure=structure,
                    selected_office=selected_office,
                )
                for off in abandoned_offices:
                    if off.is_default:
                        messages.add_message(
                            request,
                            messages.WARNING,
                            _(
                                "L'ufficio <b>{}</b> non può essere"
                                " posto in sola lettura".format(off)
                            ),
                        )
                    else:
                        ticket.update_log(
                            user=request.user,
                            note=_(
                                "Competenza trasferita da"
                                " Ufficio: {}."
                                " (L'ufficio ha mantenuto"
                                " accesso in sola lettura)".format(off)
                            ),
                        )
            # If follow and want to manage
            ticket.add_competence(office=new_office, user=request.user)
            ticket.update_log(
                user=request.user, note=_(
                    "Nuova competenza: {}").format(new_office)
            )

            # log action
            logger.info(
                "[{}] {} added new competence to"
                " ticket {}"
                " (follow: {}) (readonly: {})".format(
                    timezone.localtime(), request.user, ticket, follow, readonly
                )
            )

            return redirect(
                "uni_ticket:manage_ticket_url_detail",
                structure_slug=structure_slug,
                ticket_id=ticket_id,
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )
    user_type = get_user_type(request.user, structure)
    template = "{}/add_ticket_competence.html".format(user_type)
    title = _("Trasferisci competenza richiesta")
    sub_title = "{} ({})".format(ticket.subject, ticket_id)
    d = {
        "can_manage": can_manage,
        "offices": offices,
        "operator_offices": operator_offices_list,
        "structure": structure,
        "structure_slug": new_structure_slug,
        "strutture": strutture,
        "sub_title": sub_title,
        "ticket": ticket,
        "title": title,
    }
    return render(request, template, d)


@login_required
def ticket_message_url(request, structure_slug, ticket_id):  # pragma: no cover
    """
    Makes URL redirect to add ticket message by user role

    :type structure_slug: String
    :type ticket_id: String

    :param structure_slug: structure slug
    :param ticket_id: ticket code

    :return: redirect
    """
    structure = get_object_or_404(OrganizationalStructure, slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect(
        "uni_ticket:{}_ticket_message".format(
            user_type), structure_slug, ticket_id
    )


@login_required
@has_ticket_admin_privileges
# @ticket_is_taken_for_employee
@ticket_assigned_to_structure
# @ticket_is_taken_and_not_closed
def ticket_message(
    request,
    structure_slug,
    ticket_id,
    structure,
    can_manage,
    ticket,
    office_employee=None,
):
    """
    View ticket messages

    :type structure_slug: String
    :type ticket_id: String
    :type structure: OrganizationalStructure (from @has_ticket_admin_privileges)
    :type can_manage: Dictionary (from @has_ticket_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param structure: structure object (from @has_ticket_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_ticket_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """

    title = "{} - {}".format(_("Messaggi"), ticket.created_by)
    request.user
    user_type = get_user_type(request.user, structure)
    # Conversazione utente-operatori
    ticket_replies = TicketReply.objects.filter(ticket=ticket)
    form = ReplyForm()

    ticket_taken = ticket.has_been_taken(
        structure=structure, exclude_readonly=True)

    # if ticket.is_open() and can_manage:
    if can_manage:
        user_replies = ticket_replies.filter(
            Q(owner=ticket.created_by) | Q(owner=ticket.compiled_by),
            structure=None,
            read_by=None,
        )
        if not can_manage["readonly"] and ticket_taken:
            for reply in user_replies:
                reply.read_by = request.user
                reply.read_date = timezone.localtime()
                reply.save(update_fields=["read_by", "read_date"])

    if request.method == "POST":
        if can_manage["readonly"]:
            messages.add_message(
                request, messages.ERROR, READONLY_COMPETENCE_OVER_TICKET
            )
            return redirect(
                "uni_ticket:manage_ticket_url_detail",
                structure_slug=structure_slug,
                ticket_id=ticket_id,
            )
        if not ticket_taken:
            m = _("La richiesta deve essere prima presa in carico")
            messages.add_message(request, messages.ERROR, m)
            return redirect(
                "uni_ticket:manage_ticket_url_detail",
                structure_slug=structure_slug,
                ticket_id=ticket_id,
            )
        # Se il ticket non è aperto non è possibile scrivere
        # if not ticket.is_open(request.user):
        if ticket.is_closed:
            return custom_message(
                request,
                _("La richiesta non è modificabile"),
                structure_slug=structure.slug,
            )
        form = ReplyForm(request.POST, request.FILES)
        if form.is_valid():
            ticket_reply = form.save(commit=False)
            ticket_reply.ticket = ticket
            ticket_reply.structure = structure
            ticket_reply.owner = request.user
            ticket_reply.save()

            # log action
            logger.info(
                "[{}] {} added new message in"
                " ticket {}".format(timezone.localtime(), request.user, ticket)
            )

            log_msg = _(
                "Nuovo messaggio (da operatore {}). " "Oggetto: {} / " "Testo: {}"
            ).format(structure, ticket_reply.subject, ticket_reply.text)
            ticket.update_log(request.user, note=log_msg, send_mail=False)

            # Send mail to ticket owner
            mail_params = {
                "hostname": settings.HOSTNAME,
                "status": _("ricevuto"),
                "message_subject": ticket_reply.subject,
                "message_text": ticket_reply.text,
                "ticket": ticket,
                "user": ticket.created_by,
                "url": request.build_absolute_uri(
                    reverse(
                        "uni_ticket:ticket_message", kwargs={"ticket_id": ticket.code}
                    )
                ),
            }
            m_subject = _(
                "{} - richiesta {} nuovo messaggio".format(
                    settings.HOSTNAME, ticket)
            )
            send_custom_mail(
                subject=m_subject,
                recipients=ticket.get_owners(),
                body=USER_TICKET_MESSAGE,
                params=mail_params,
            )
            # END Send mail to ticket owner

            messages.add_message(
                request, messages.SUCCESS, _("Messaggio inviato con successo")
            )
            return redirect(
                "uni_ticket:manage_ticket_message_url",
                structure_slug=structure_slug,
                ticket_id=ticket_id,
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )
    d = {
        "form": form,
        "structure": structure,
        "sub_title": ticket.__str__(),
        "sub_title_2": ticket.description,
        "ticket": ticket,
        "ticket_replies": ticket_replies,
        "title": title,
    }
    template = "{}/ticket_assistance.html".format(user_type)
    return render(request, template, d)


@login_required
def task_add_new_url(request, structure_slug, ticket_id):  # pragma: no cover
    """
    Makes URL redirect to add new ticket task according to user role

    :type structure_slug: String
    :type ticket_id: String

    :param structure_slug: structure slug
    :param ticket_id: ticket code

    :return: redirect
    """
    structure = get_object_or_404(OrganizationalStructure, slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect(
        "uni_ticket:{}_add_ticket_task".format(
            user_type), structure_slug, ticket_id
    )


@login_required
@has_ticket_admin_privileges
@ticket_is_taken_for_employee
@ticket_assigned_to_structure
@ticket_is_taken_and_not_closed
def task_add_new(
    request,
    structure_slug,
    ticket_id,
    structure,
    can_manage,
    ticket,
    office_employee=None,
):
    """
    Add new ticket task

    :type structure_slug: String
    :type ticket_id: String
    :type structure: OrganizationalStructure (from @has_ticket_admin_privileges)
    :type can_manage: Dictionary (from @has_ticket_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param structure: structure object (from @has_ticket_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_ticket_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    user_type = get_user_type(request.user, structure)
    template = "{}/add_ticket_task.html".format(user_type)
    title = _("Aggiungi Attività")
    sub_title = "{} ({})".format(ticket.subject, ticket_id)
    form = TaskForm()
    if request.method == "POST":
        form = TaskForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_task = form.save(commit=False)
            new_task.ticket = ticket
            new_task.created_by = request.user
            new_task.code = uuid_code()
            new_task.save()

            # log action
            logger.info(
                "[{}] {} created new task {}".format(
                    timezone.localtime(), request.user, new_task
                )
            )

            ticket.update_log(
                user=request.user, note=_(
                    "Aggiunta attività: {}".format(new_task))
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Attività {} creata con successo".format(new_task)),
            )
            return redirect(
                "uni_ticket:manage_ticket_url_detail",
                structure_slug=structure_slug,
                ticket_id=ticket.code,
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )
    d = {
        "form": form,
        "structure": structure,
        "sub_title": sub_title,
        "ticket": ticket,
        "title": title,
    }
    return render(request, template, d)


@login_required
@has_ticket_admin_privileges
@ticket_is_taken_for_employee
@ticket_assigned_to_structure
@ticket_is_taken_and_not_closed
def task_remove(
    request, structure_slug, ticket_id, task_id, structure, can_manage, ticket
):
    """
    Remove ticket task

    :type structure_slug: String
    :type ticket_id: String
    :type task_id: String
    :type structure: OrganizationalStructure (from @has_ticket_admin_privileges)
    :type can_manage: Dictionary (from @has_ticket_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param task_id: task code
    :param structure: structure object (from @has_ticket_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_ticket_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)

    :return: render
    """
    get_user_type(request.user, structure)
    task = get_object_or_404(Task, code=task_id, ticket=ticket)

    # log action
    logger.error(
        "[{}] {} tried to"
        " removed task {}"
        " in ticket {}".format(timezone.localtime(),
                               request.user, task, ticket)
    )

    task.delete()
    ticket.update_log(user=request.user, note=_(
        "Rimossa attività: {}".format(task)))
    messages.add_message(
        request, messages.SUCCESS, _(
            "Attività {} rimossa correttamente".format(task))
    )
    return redirect(
        "uni_ticket:manage_ticket_url_detail",
        structure_slug=structure_slug,
        ticket_id=ticket_id,
    )


@login_required
def task_detail_url(request, structure_slug, ticket_id, task_id):  # pragma: no cover
    """
    Makes URL redirect to view ticket task details according to user role

    :type structure_slug: String
    :type ticket_id: String
    :type task_id: String

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param task_id: task code

    :return: redirect
    """
    structure = get_object_or_404(OrganizationalStructure, slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect(
        "uni_ticket:{}_task_detail".format(user_type),
        structure_slug=structure_slug,
        ticket_id=ticket_id,
        task_id=task_id,
    )


@login_required
@has_ticket_admin_privileges
@ticket_assigned_to_structure
def task_detail(
    request,
    structure_slug,
    ticket_id,
    task_id,
    structure,
    can_manage,
    ticket,
    office_employee=None,
):
    """
    View task details

    :type structure_slug: String
    :type ticket_id: String
    :type task_id: String
    :type structure: OrganizationalStructure (from @has_ticket_admin_privileges)
    :type can_manage: Dictionary (from @has_ticket_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param task_id: task code
    :param structure: structure object (from @has_ticket_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_ticket_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    task = get_object_or_404(Task, code=task_id, ticket=ticket)
    title = _("Dettaglio attività")
    priority = task.get_priority()
    # allegati = ticket.get_allegati_dict()
    task_logs = LogEntry.objects.filter(
        content_type_id=ContentType.objects.get_for_model(
            task).pk, object_id=task.pk
    )
    form = PriorityForm(data={"priorita": task.priority})
    if request.method == "POST":
        if can_manage["readonly"]:

            # log action
            logger.error(
                "[{}] {} tried to"
                " edit task {}"
                " in readonly ticket {}".format(
                    timezone.localtime(), request.user, task, ticket
                )
            )

            messages.add_message(
                request, messages.ERROR, READONLY_COMPETENCE_OVER_TICKET
            )
            return redirect(
                "uni_ticket:manage_ticket_url_detail",
                structure_slug=structure_slug,
                ticket_id=ticket_id,
            )
        if task.is_closed:
            # log action
            logger.error(
                "[{}] {} tried to"
                " edit closed task {}".format(
                    timezone.localtime(), request.user, task)
            )

            messages.add_message(
                request, messages.ERROR, _(
                    "Impossibile modificare un'attività chiusa")
            )
            return redirect(
                "uni_ticket:manage_task_detail_url",
                structure_slug=structure_slug,
                ticket_id=ticket_id,
                task_id=task_id,
            )

        form = PriorityForm(request.POST)
        if form.is_valid():
            priority = form.cleaned_data["priorita"]
            priority_text = dict(PRIORITY_LEVELS).get(priority)
            msg = _("Task {} - Priorità assegnata: {}".format(task, priority_text))
            task.priority = priority
            task.save(update_fields=["priority"])
            task.update_log(user=request.user, note=msg)
            ticket.update_log(user=request.user, note=msg)

            # log action
            logger.error(
                "[{}] {} tried to"
                " edited task {}"
                " priority to {}".format(
                    timezone.localtime(), request.user, task, priority_text
                )
            )

            messages.add_message(
                request, messages.SUCCESS, _(
                    "Attività aggiornata con successo")
            )
            return redirect(
                "uni_ticket:manage_task_detail_url",
                structure_slug=structure_slug,
                ticket_id=ticket_id,
                task_id=task_id,
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )
    d = {
        "form": form,
        "priority": priority,
        "structure": structure,
        "sub_title": task,
        "task": task,
        "logs": task_logs,
        "title": title,
    }
    user_type = get_user_type(request.user, structure)
    template = "{}/task_detail.html".format(user_type)
    return render(request, template, d)


@login_required
def task_close_url(request, structure_slug, ticket_id, task_id):  # pragma: no cover
    """
    Makes URL redirect to close ticket task details according to user role

    :type structure_slug: String
    :type ticket_id: String
    :type task_id: String

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param task_id: task code

    :return: redirect
    """
    structure = get_object_or_404(OrganizationalStructure, slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect(
        "uni_ticket:{}_close_task".format(user_type),
        structure_slug=structure_slug,
        ticket_id=ticket_id,
        task_id=task_id,
    )


@login_required
@has_ticket_admin_privileges
@ticket_is_taken_for_employee
@ticket_assigned_to_structure
@ticket_is_taken_and_not_closed
def task_close(
    request,
    structure_slug,
    ticket_id,
    task_id,
    structure,
    can_manage,
    ticket,
    office_employee=None,
):
    """
    Closes task details

    :type structure_slug: String
    :type ticket_id: String
    :type task_id: String
    :type structure: OrganizationalStructure (from @has_ticket_admin_privileges)
    :type can_manage: Dictionary (from @has_ticket_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param task_id: task code
    :param structure: structure object (from @has_ticket_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_ticket_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    # Se il ticket non è chiudibile (per dipendenze attive)
    task = get_object_or_404(Task, code=task_id, ticket=ticket)
    if task.is_closed:
        return custom_message(
            request, _("Attività già chiusa!"), structure_slug=structure.slug
        )
    if ticket.is_closed:
        return custom_message(
            request,
            _("La richiesta {} è chiusa".format(ticket)),
            structure_slug=structure.slug,
        )

    title = _("Chiusura dell'attività")
    sub_title = task
    form = TaskCloseForm()
    if request.method == "POST":
        form = TaskCloseForm(request.POST)
        if form.is_valid():
            motivazione = form.cleaned_data["note"]
            closing_status = form.cleaned_data["status"]
            task.is_closed = True
            task.closed_by = request.user
            task.closing_reason = motivazione
            task.closing_status = closing_status
            task.closed_date = timezone.localtime()
            task.save(
                update_fields=[
                    "is_closed",
                    "closing_reason",
                    "closing_status",
                    "closed_date",
                    "closed_by",
                ]
            )

            # log action
            logger.info(
                "[{}] {} closed task {}".format(
                    timezone.localtime(), request.user, task
                )
            )

            msg = _(
                "Chiusura attività ({}): {} - {}".format(
                    task, dict(CLOSING_LEVELS).get(closing_status), motivazione
                )
            )
            task.update_log(user=request.user, note=msg)
            ticket.update_log(user=request.user, note=msg)
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Attività {} chiusa correttamente".format(task)),
            )
            return redirect(
                "uni_ticket:manage_ticket_url_detail",
                structure_slug=structure_slug,
                ticket_id=ticket_id,
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )
    user_type = get_user_type(request.user, structure)
    template = "{}/task_close.html".format(user_type)
    d = {
        "form": form,
        "structure": structure,
        "sub_title": sub_title,
        "task": task,
        "title": title,
    }
    return render(request, template, d)


@login_required
@has_ticket_admin_privileges
@ticket_is_taken_for_employee
@ticket_assigned_to_structure
@ticket_is_taken_and_not_closed
def task_reopen(
    request, structure_slug, ticket_id, task_id, structure, can_manage, ticket
):
    """
    Reopen task

    :type structure_slug: String
    :type ticket_id: String
    :type task_id: String
    :type structure: OrganizationalStructure (from @has_ticket_admin_privileges)
    :type can_manage: Dictionary (from @has_ticket_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param task_id: task code
    :param structure: structure object (from @has_ticket_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_ticket_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)

    :return: redirect
    """
    task = get_object_or_404(Task, code=task_id, ticket=ticket)
    # Se il ticket non è chiuso blocca
    if not task.is_closed:
        return custom_message(
            request, _("L'attività non è stata chiusa"), structure_slug=structure.slug
        )
    if ticket.is_closed:
        # log action
        logger.error(
            "[{}] {} tried to"
            " remove task {}"
            " in closed ticket {}".format(
                timezone.localtime(), request.user, task, ticket
            )
        )
        return custom_message(
            request,
            _("La richiesta {} è chiusa").format(ticket),
            structure_slug=structure.slug,
        )

    task.is_closed = False
    task.save(update_fields=["is_closed"])
    msg = _("Riapertura attività {}".format(task))
    task.update_log(user=request.user, note=msg)

    # log action
    logger.error(
        "[{}] {} tried to"
        " reopened task {}"
        " in closed ticket {}".format(
            timezone.localtime(), request.user, task, ticket)
    )

    ticket.update_log(user=request.user, note=msg)
    messages.add_message(
        request, messages.SUCCESS, _(
            "Attività {} riaperta correttamente".format(task))
    )
    return redirect(
        "uni_ticket:manage_ticket_url_detail",
        structure_slug=structure_slug,
        ticket_id=ticket_id,
    )


@login_required
def task_edit_url(request, structure_slug, ticket_id, task_id):  # pragma: no cover
    """
    Makes URL redirect to edit ticket task according to user role

    :type structure_slug: String
    :type ticket_id: String
    :type task_id: String

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param task_id: task code

    :return: redirect
    """
    structure = get_object_or_404(OrganizationalStructure, slug=structure_slug)
    user_type = get_user_type(request.user, structure)
    return redirect(
        "uni_ticket:{}_edit_task".format(user_type),
        structure_slug=structure_slug,
        ticket_id=ticket_id,
        task_id=task_id,
    )


@login_required
@has_ticket_admin_privileges
@ticket_is_taken_for_employee
@ticket_assigned_to_structure
@ticket_is_taken_and_not_closed
def task_edit(
    request,
    structure_slug,
    ticket_id,
    task_id,
    structure,
    can_manage,
    ticket,
    office_employee=None,
):
    """
    Edit task details

    :type structure_slug: String
    :type ticket_id: String
    :type task_id: String
    :type structure: OrganizationalStructure (from @has_ticket_admin_privileges)
    :type can_manage: Dictionary (from @has_ticket_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param task_id: task code
    :param structure: structure object (from @has_ticket_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_ticket_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    task = get_object_or_404(Task, code=task_id, ticket=ticket)
    usertype = get_user_type(request.user, structure)
    form = TaskForm(instance=task)

    template = "{}/task_edit.html".format(usertype)
    title = _("Modifica attività")
    sub_title = task
    allegati = {}
    if task.attachment:
        allegati[form.fields["attachment"].label.lower()] = os.path.basename(
            task.attachment.name
        )
        del form.fields["attachment"]

    if request.method == "POST":
        if task.is_closed:
            # log action
            logger.error(
                "[{}] {} tried to"
                " edit closed task {}".format(
                    timezone.localtime(), request.user, task)
            )

            messages.add_message(
                request, messages.ERROR, _(
                    "Impossibile modificare un'attività chiusa")
            )
            return redirect(
                "uni_ticket:manage_task_detail_url",
                structure_slug=structure_slug,
                ticket_id=ticket_id,
                task_id=task_id,
            )

        form = TaskForm(instance=task, data=request.POST, files=request.FILES)

        if form.is_valid():
            msg = _("Modifica attività {}".format(task))
            if task.priority != form.cleaned_data["priority"]:
                msg = msg + _(
                    " e Priorità assegnata: {}"
                    "".format(dict(PRIORITY_LEVELS).get(
                        form.cleaned_data["priority"]))
                )
            form.save()

            # log action
            logger.info(
                "[{}] {} edited task {}".format(
                    timezone.localtime(), request.user, task
                )
            )

            task.update_log(user=request.user, note=msg)
            ticket.update_log(user=request.user, note=msg)
            messages.add_message(
                request, messages.SUCCESS, _(
                    "Attività aggiornata con successo")
            )
            return redirect(
                "uni_ticket:edit_task",
                structure_slug=structure_slug,
                ticket_id=ticket_id,
                task_id=task_id,
            )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )

    d = {
        "allegati": allegati,
        "form": form,
        "structure": structure,
        "sub_title": sub_title,
        "task": task,
        "title": title,
    }
    return render(request, template, d)


@login_required
@has_ticket_admin_privileges
@ticket_is_taken_for_employee
@ticket_assigned_to_structure
@ticket_is_taken_and_not_closed
def task_attachment_delete(
    request,
    structure_slug,
    ticket_id,
    task_id,
    structure,
    can_manage,
    ticket,
    office_employee=None,
):
    """
    Delete a task attachment (it must be called by a dialog to confirm action)

    :type structure_slug: String
    :type ticket_id: String
    :type task_id: String
    :type structure: OrganizationalStructure (from @has_ticket_admin_privileges)
    :type can_manage: Dictionary (from @has_ticket_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param task_id: task code
    :param structure: structure object (from @has_ticket_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_ticket_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: redirect
    """
    task = get_object_or_404(Task, code=task_id, ticket=ticket)
    if task.created_by != request.user:
        return custom_message(
            request,
            _("Permessi di modifica dell'attività mancanti"),
            structure_slug=structure.slug,
        )

    # Rimuove l'allegato dal disco
    delete_directory(task.get_folder())

    task.attachment = None
    task.save(update_fields=["attachment"])

    msg = _("Allegato attività {} eliminato".format(task.code))
    task.update_log(user=request.user, note=_("Allegato eliminato"))
    ticket.update_log(user=request.user, note=msg)

    # log action
    logger.info(
        "[{}] {} deleted attachment"
        " from task {}".format(timezone.localtime(), request.user, task)
    )

    messages.add_message(request, messages.SUCCESS, msg)
    return redirect(
        "uni_ticket:edit_task",
        structure_slug=structure.slug,
        ticket_id=ticket_id,
        task_id=task_id,
    )


@login_required
@has_ticket_admin_privileges
@ticket_assigned_to_structure
def ticket_taken_by_unassigned_offices(
    request, structure_slug, ticket_id, structure, can_manage, ticket
):
    offices = ticket.is_untaken_by_user_offices(
        user=request.user, structure=structure)
    for office in offices:
        assignment = TicketAssignment.objects.filter(
            ticket=ticket, office=office, taken_date__isnull=True
        ).first()
        assignment.taken_by = request.user
        assignment.taken_date = timezone.localtime()
        assignment.save(update_fields=["modified", "taken_date", "taken_by"])

        msg = _(
            "Ticket {} correttamente "
            "assegnato a Ufficio: {} [{}]".format(ticket, office, request.user)
        )
        ticket.update_log(user=request.user, note=msg)
        messages.add_message(request, messages.SUCCESS, msg)
    return redirect(
        "uni_ticket:manage_ticket_url_detail",
        structure_slug=structure_slug,
        ticket_id=ticket_id,
    )


@login_required
@has_ticket_admin_privileges
# @ticket_is_taken_for_employee
@ticket_assigned_to_structure
@ticket_is_taken_and_not_closed
def ticket_competence_leave(
    request,
    structure_slug,
    ticket_id,
    structure,
    can_manage,
    ticket,
    office_employee=None,
):
    """
    Leaves single office ticket competence

    :type structure_slug: String
    :type ticket_id: String
    :type structure: OrganizationalStructure (from @has_ticket_admin_privileges)
    :type can_manage: Dictionary (from @has_ticket_admin_privileges)
    :type ticket: Ticket (from @ticket_assigned_to_structure)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param ticket_id: ticket code
    :param structure: structure object (from @has_ticket_admin_privileges)
    :param can_manage: if user can manage or can read only (from @has_ticket_admin_privileges)
    :param ticket: ticket object (from @ticket_assigned_to_structure)
    :param office_employee: operator offices queryset (from @is_operator)

    :return: render
    """
    form = TicketOperatorOfficesForm(
        structure=structure, operator=request.user, ticket=ticket
    )
    user_type = get_user_type(request.user, structure)
    template = "{}/leave_ticket_competence.html".format(user_type)
    title = _("Abbandona competenza richiesta")
    sub_title = _(
        "Seleziona l'ufficio che deve abbandonare " 'la competenza sulla richiesta "{}"'
    ).format(ticket.subject)

    if request.method == "POST":
        form = TicketOperatorOfficesForm(
            data=request.POST, structure=structure, operator=request.user, ticket=ticket
        )
        if form.is_valid():
            office = form.cleaned_data["office"]
            assignments = (
                TicketAssignment.objects.filter(
                    ticket=ticket, follow=True, readonly=False, office__is_active=True
                )
                .exclude(office=office)
                .count()
            )
            # there are other offices managing ticket
            if assignments > 0:
                assignment_to_disable = TicketAssignment.objects.get(
                    ticket=ticket, office=office
                )
                assignment_to_disable.follow = False
                assignment_to_disable.readonly = False
                assignment_to_disable.save(
                    update_fields=["follow", "readonly"])

                logger.info(
                    "[{}] {} removed competence of office {}"
                    " for ticket {}".format(
                        timezone.localtime(), request.user, office, ticket
                    )
                )

                ticket.update_log(
                    user=request.user,
                    note=_("Competenza abbandonata da" " Ufficio: {}".format(office)),
                )

                messages.add_message(
                    request,
                    messages.SUCCESS,
                    _(
                        "Competenza ufficio <b>{}</b> "
                        "abbandonata con successo"
                        "".format(office)
                    ),
                )
            # this is the only office managing ticket
            else:
                messages.add_message(
                    request,
                    messages.ERROR,
                    _(
                        "<b>Operazione non consentita</b>"
                        "<br>"
                        "Rimuovendo la competenza "
                        " di <b>{}</b>, "
                        "la ichiesta non sarebbe più gestita "
                        "da alcun ufficio. "
                        ""
                    ).format(office),
                )
            return redirect(
                "uni_ticket:manage_ticket_url_detail",
                structure_slug=structure_slug,
                ticket_id=ticket_id,
            )

    d = {
        "form": form,
        "structure": structure,
        "sub_title": sub_title,
        "ticket": ticket,
        "title": title,
    }
    return render(request, template, d)


@login_required
def export_detailed_report(request, structure_slug):
    if request.POST:
        # get structure
        structure = get_object_or_404(
            OrganizationalStructure, slug=structure_slug, is_active=True
        )
        # get and check user privileges on structure
        user_type = get_user_type(user=request.user, structure=structure)
        if user_type == "user":
            return custom_message(request, _("Forbidden"), 403)
        office_employee_list = user_is_operator(request.user, structure)
        offices = user_offices_list(office_employee_list)

        # ticket codes from post
        ticket_codes = request.POST.getlist("ticket_code")
        ticket_list = []
        categories = []

        # check if user can access to these tickets (avoid force POST)
        for ticket_code in ticket_codes:

            ticket = Ticket.objects.filter(code=ticket_code).first()
            if not ticket:
                continue
            access_ok = (
                user_type == "manager" and ticket.is_followed_in_structure(
                    structure)
            ) or (
                user_type == "operator"
                and ticket.is_followed_by_one_of_offices(offices=offices)
            )
            if not access_ok:
                continue
            ticket_list.append(ticket)
            if ticket.input_module.ticket_category not in categories:
                categories.append(ticket.input_module.ticket_category)

        # export categories zip files
        if categories:
            output = io.BytesIO()
            f = zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED)

            for cat in categories:
                try:
                    cat_zip = export_category_zip(cat, ticket_codes)
                    if len(categories) == 1:
                        return cat_zip
                    f.writestr(cat.name.replace("/", "_") +
                               ".zip", cat_zip.content)
                except:
                    continue
            f.close()
            response = HttpResponse(
                output.getvalue(), content_type="application/zip")
            response[
                "Content-Disposition"
            ] = 'attachment; filename="uniticket_{}.zip"'.format(timezone.localtime())
            return response
        return custom_message(request, _("Nessun record da esportare"))
    return custom_message(request, _("Forbidden"), 403)

@login_required
def statistics(request, structure_slug:str = None, structure: OrganizationalStructure = None):
    """
    uniTicket general statistics per structure
    """
    _default_start = timezone.localtime() - timezone.timedelta(days=STATS_DEFAULT_DATE_START_DELTA_DAYS)
    date_start = _default_start
    _default_end = timezone.localtime()
    date_end = _default_end

    if request.POST.get('date_start'):
        date_start = timezone.datetime.strptime(request.POST['date_start'], '%Y-%m-%d')
        date_start = timezone.make_aware(date_start)

    if request.POST.get('date_end'):
        date_end = timezone.datetime.strptime(request.POST['date_end'], '%Y-%m-%d')
        # X/Y/ZZZ 00:00:00 => X/Y/ZZZZ 23:59:59
        date_end = timezone.make_aware(date_end) + timezone.timedelta(days = 1) - timezone.timedelta(seconds = 1)

    if date_start > date_end:
        date_start = _default_start
        date_end = _default_end
        messages.add_message(
            request, messages.ERROR,
            _(
                "La data di inizio non può essere successiva a quella di fine. "
                "La data di inizio è stata corretta a <b>{}</b> e quella di fine a <b>{}</b>"
            ).format(
                _default_start.strftime(settings.DEFAULT_DATE_FORMAT),
                _default_end.strftime(settings.DEFAULT_DATE_FORMAT)
            )
        )

    if (date_end - date_start).days > STATS_MAX_DAYS:
        date_start = _default_start
        messages.add_message(
            request, messages.WARNING,
            _(
                "La finestra oraria massima per le statistiche è di {} giorni. "
                "La data di inizio è stata corretta a <b>{}</b>"
            ).format(
                STATS_MAX_DAYS,
                _default_start.strftime(settings.DEFAULT_DATE_FORMAT)
            )
        )

    _q = dict(
        date_start = date_start,
        date_end = date_end,
        structure_slug = structure_slug
    )
    if request.POST.get('office_slug'):
        _q['office_slug'] = request.POST['office_slug']
    if request.POST.get('category_slug'):
        _q['category_slug'] = request.POST['category_slug']

    stats = uniTicketStats(**_q)
    stats.load()

    _struct = (
        structure or
        OrganizationalStructure.objects.filter(structure__slug = structure_slug).first()
    )

    context = {
        "stats" : stats,
        "structure" : _struct,
        "title" : _("Statistiche"),
        "sub_title" : _("Struttura {} - dal {} al {}").format(
            structure,
            date_start.strftime(settings.DEFAULT_DATE_FORMAT),
            date_end.strftime(settings.DEFAULT_DATE_FORMAT)
        ),
        "date_start": date_start.strftime(settings.DEFAULT_DATE_FORMAT),
        "date_end": date_end.strftime(settings.DEFAULT_DATE_FORMAT),
        "JS_CHART_CDN_URL": JS_CHART_CDN_URL,
        # "ticket_per_day": tuple(stats.ticket_per_day.keys()),
        "ticket_per_day": stats.ticket_per_day,
        "time_slots": STATS_TIME_SLOTS,
        "ticket" : request.POST.get('category_slug'),
        "office" : request.POST.get('office_slug'),
        "STATS_HEAT_MAP_RANGES": json.dumps(STATS_HEAT_MAP_RANGES, indent=2)
    }
    if _struct:
        context['offices'] = _struct.get_offices()
        context['operators'] = _struct.get_employees()
        context["tickets"] = TicketCategory.objects.filter(organizational_structure=_struct)

    return render(request, "management/statistics.html", context)
