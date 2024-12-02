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

from . generic import *


logger = logging.getLogger(__name__)


class TicketAPIUnassignedCounter(TicketAPIBaseView):
    def get(self, request, structure_slug, *args, **kwargs):
        structure = get_object_or_404(OrganizationalStructure, slug=structure_slug)
        oe = user_is_operator(request.user, structure)
        if not oe: raise PermissionDenied
        unassigned_tickets = visible_tickets_to_user(user=request.user,
                                                     structure=structure,
                                                     office_employee=oe,
                                                     closed=False,
                                                     taken=False)
        return Response({'count': unassigned_tickets.count()})


class TicketAPIOpenCounter(TicketAPIBaseView):
    def get(self, request, structure_slug, *args, **kwargs):
        structure = get_object_or_404(OrganizationalStructure, slug=structure_slug)
        oe = user_is_operator(request.user, structure)
        if not oe: raise PermissionDenied
        open_tickets = visible_tickets_to_user(user=request.user,
                                               structure=structure,
                                               office_employee=oe,
                                               closed=False,
                                               taken=True)
        return Response({'count': open_tickets.count()})


class TicketAPIMyOpenCounter(TicketAPIBaseView):
    def get(self, request, structure_slug, *args, **kwargs):
        structure = get_object_or_404(OrganizationalStructure, slug=structure_slug)
        oe = user_is_operator(request.user, structure)
        if not oe: raise PermissionDenied
        my_open_tickets = visible_tickets_to_user(user=request.user,
                                                  structure=structure,
                                                  office_employee=oe,
                                                  closed=False,
                                                  taken=True,
                                                  taken_by=request.user)
        return Response({'count': my_open_tickets.count()})


class TicketAPIMessagesCounter(TicketAPIBaseView):
    def get(self, request, structure_slug, *args, **kwargs):
        structure = get_object_or_404(OrganizationalStructure, slug=structure_slug)
        oe = user_is_operator(request.user, structure)
        if not oe: raise PermissionDenied
        ticket_ids = visible_tickets_to_user(
            user=request.user,
            structure=structure,
            office_employee=oe,
            closed=False
        )
        messages = TicketReply.get_unread_messages_count(ticket_ids=ticket_ids)
        return Response({'count': messages})
