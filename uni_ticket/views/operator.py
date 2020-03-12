from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.translation import gettext as _

from organizational_area.models import *

from uni_ticket.decorators import is_operator
from uni_ticket.models import *
from uni_ticket.settings import OPERATOR_PREFIX
from uni_ticket.utils import (user_is_operator,
                              user_offices_list,
                              visible_tickets_to_user)

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
    sub_title = _("Gestisci i ticket in modalità {}").format(OPERATOR_PREFIX)
    template = "operator/dashboard.html"
    offices = user_offices_list(office_employee)
    user_tickets = visible_tickets_to_user(user=request.user,
                                           structure=structure,
                                           office_employee=office_employee)
    tickets = Ticket.objects.filter(code__in=user_tickets)
    non_gestiti = tickets.filter(is_taken=False,
                                 is_closed=False)
    aperti = tickets.filter(is_taken=True, is_closed=False)
    chiusi = tickets.filter(is_closed=True)

    messages = 0
    for ticket in tickets:
        if not ticket.is_followed_by_one_of_offices(offices):
            continue
        messages += ticket.get_messages_count()[1]

    d = {'ticket_messages': messages,
         'offices': offices,
         'structure': structure,
         'sub_title': sub_title,
         'title': title,
         'ticket_aperti': aperti,
         'ticket_chiusi': chiusi,
         'ticket_non_gestiti': non_gestiti,}
    return render(request, template, d)
