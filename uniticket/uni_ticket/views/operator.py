from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from organizational_area.models import *

from uni_ticket.decorators import is_operator
from uni_ticket.models import *
from uni_ticket.settings import OPERATOR_PREFIX
from uni_ticket.utils import base_context, user_offices_list, visible_tickets_to_user


@login_required
@is_operator
def dashboard(request, structure_slug):
    """
    Operator Dashboard

    :type structure_slug: String

    :param structure_slug: structure slug

    :return: render
    """
    # from @is_operator
    structure = request.structure
    office_employee = request.office_employee
    
    title = _("Pannello di Controllo")
    sub_title = _("Gestisci le richieste in modalità {}").format(
        OPERATOR_PREFIX)
    template = "operator/dashboard.html"
    offices = user_offices_list(office_employee)

    d = {
        "offices": offices,
        "structure": structure,
        "sub_title": sub_title,
        "title": title,
        # "ticket_messages": messages,
    }
    return render(request, template, base_context(d))
