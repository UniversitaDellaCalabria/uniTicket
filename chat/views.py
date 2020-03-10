from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _

from organizational_area.models import OrganizationalStructure
from uni_ticket.models import TicketCategory
from uni_ticket.utils import (custom_message,
                              user_is_employee,
                              user_is_in_organization)

from . views import *


# @login_required
# def index(request):
    # return render(request, 'chat/index.html', {})

@login_required
def room(request, room_name):
    structure = get_object_or_404(OrganizationalStructure,
                                  slug=room_name,
                                  is_active=True)
    categorie = TicketCategory.objects.filter(organizational_structure=structure.pk,
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

    if categorie:
        return render(request, 'chat/room.html', {
            'room_name': room_name
        })
    return custom_message(request, _("Questa struttura non offre "
                                     "categorie disponibili per la tua "
                                     "tipologia di utenza"),
                          structure_slug=structure.slug)
