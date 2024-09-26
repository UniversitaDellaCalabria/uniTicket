import logging

from django.contrib import messages
from django.core import serializers
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404

from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, viewsets

from uni_ticket.models import Ticket, TicketAssignment, TicketCategory, TicketReply
from uni_ticket.utils import user_is_manager, user_is_operator, visible_tickets_to_user

from organizational_area.models import OrganizationalStructure
from api_rest.authorizations import AuthorizationToken

from . generic import *


logger = logging.getLogger(__name__)


class TicketAPICounter(TicketAPIBaseView):
    def get(self, request, structure_slug, *args, **kwargs):
        structure = get_object_or_404(OrganizationalStructure, slug=structure_slug)
        if not user_is_manager(request.user, structure): raise PermissionDenied

        unassigned_tickets = TicketAssignment.get_ticket_per_structure(structure=structure,
                                                                       closed=False,
                                                                       taken=False)

        open_tickets = TicketAssignment.get_ticket_per_structure(structure=structure,
                                                                 closed=False,
                                                                 taken=True)

        my_open_tickets = TicketAssignment.get_ticket_per_structure(structure=structure,
                                                                    closed=False,
                                                                    taken=True,
                                                                    taken_by=request.user)
        ticket_ids = TicketAssignment.objects.filter(
            office__organizational_structure=structure,
            office__is_active=True,
            follow=True,
            ticket__is_closed=False
        ).values_list('ticket__pk', flat=True).distinct()
        messages = TicketReply.get_unread_messages_count(ticket_ids=ticket_ids)

        return Response({'unassigned': len(unassigned_tickets),
                         'open': len(open_tickets),
                         'my_open': len(my_open_tickets),
                         'new_messages': messages})
