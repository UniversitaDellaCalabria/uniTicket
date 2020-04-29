import random

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils.translation import gettext as _

from organizational_area.models import OrganizationalStructure
from uni_ticket.models import TicketCategory
from uni_ticket.utils import (custom_message,
                              get_user_type,
                              user_is_employee,
                              user_is_in_organization,
                              user_is_in_default_office)

from . models import UserChannel
from . utils import chat_operator_online
from . views import *


@login_required
def room(request, room_name):
    structure = get_object_or_404(OrganizationalStructure,
                                  slug=room_name,
                                  is_active=True)
    user_type = get_user_type(request.user, structure)
    user_is_operator = user_is_in_default_office(request.user, structure)
    if user_is_operator:
        return render(request, 'room_{}.html'.format(user_type), {
            'structure': structure,
            'title': '{} [chat-room]'.format(structure),
            'ws_protocol': getattr(settings, 'WS_PROTOCOL', 'ws://')
        })

    if not user_is_operator and not chat_operator_online(request.user, structure.slug):
            return custom_message(request, _("Nessun operator online. "
                                             "Chat inaccessibile"),
                                  structure_slug=structure.slug)

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

    if categorie:
        return render(request, 'room_{}.html'.format(user_type), {
            'structure': structure,
            'title': '{} [chat-room]'.format(structure),
            'ws_protocol': getattr(settings, 'WS_PROTOCOL', 'ws://')
        })
    return custom_message(request, _("Questa struttura non offre "
                                     "categorie disponibili per la tua "
                                     "tipologia di utenza"),
                          structure_slug=structure.slug)

# no login is required
def random_vc_provider(request):
    return HttpResponse(random.choice(settings.VIDEOCONF_PROVIDERS))
