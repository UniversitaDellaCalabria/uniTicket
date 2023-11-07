from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext as _

from organizational_area.models import *

from uni_ticket.decorators import is_operator
from uni_ticket.models import *
from uni_ticket.settings import OPERATOR_PREFIX
from uni_ticket.utils import base_context, user_offices_list, visible_tickets_to_user


@login_required
@is_operator
def dashboard(request, structure_slug, structure, office_employee):
    """
    Operator Dashboard

    :type structure_slug: String
    :type structure: OrganizationalStructure (from @is_operator)
    :type office_employee: OrganizationalStructureOfficeEmployee (from @is_operator)

    :param structure_slug: structure slug
    :param structure: structure object (from @is_operator)
    :param office_employee: employe offices queryset (from @is_operator)

    :return: render
    """
    title = _("Pannello di Controllo")
    sub_title = _("Gestisci le richieste in modalità {}").format(
        OPERATOR_PREFIX)
    template = "operator/dashboard.html"
    offices = user_offices_list(office_employee)

    unassigned = len(visible_tickets_to_user(user=request.user,
                                             structure=structure,
                                             office_employee=office_employee,
                                             closed=False,
                                             taken=False))

    opened = len(visible_tickets_to_user(user=request.user,
                                         structure=structure,
                                         office_employee=office_employee,
                                         closed=False,
                                         taken=True))

    my_opened = len(visible_tickets_to_user(user=request.user,
                                            structure=structure,
                                            office_employee=office_employee,
                                            closed=False,
                                            taken=True,
                                            taken_by=request.user))

    ticket_codes = TicketAssignment.objects.filter(
                        office__organizational_structure=structure,
                        office__is_active=True,
                        follow=True,
                        ticket__is_closed=False,
                        office_employee=office_employee,
                    ).values_list('ticket__code', flat=True).distinct()

    messages = TicketReply.get_unread_messages_count(ticket_codes=ticket_codes)
    d = {
        "offices": offices,
        "structure": structure,
        "sub_title": sub_title,
        "title": title,
        "ticket_aperti": opened,
        "ticket_assegnati_a_me": my_opened,
        "ticket_messages": messages,
        "ticket_non_gestiti": unassigned,
    }
    return render(request, template, base_context(d))
