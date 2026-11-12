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
    """Counts the open tickets visible to an operator and not yet taken."""
    def get(self, request, structure_slug, *args, **kwargs):
        """
        Returns the number of open tickets visible to the user not yet taken.

        Raises PermissionDenied if the user is not an operator of the structure.

        Args:
            request: The current HttpRequest.

        Returns:
            A Response with the "count" key.
        """
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
    """Counts the open tickets visible to an operator and already taken."""
    def get(self, request, structure_slug, *args, **kwargs):
        """
        Returns the number of open tickets visible to the user already taken.

        Raises PermissionDenied if the user is not an operator of the structure.

        Args:
            request: The current HttpRequest.

        Returns:
            A Response with the "count" key.
        """
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
    """Counts the open tickets visible to an operator and taken by them."""
    def get(self, request, structure_slug, *args, **kwargs):
        """
        Returns the number of open tickets visible to the user taken by them.

        Raises PermissionDenied if the user is not an operator of the structure.

        Args:
            request: The current HttpRequest.

        Returns:
            A Response with the "count" key.
        """
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
    """Tells an operator whether the open tickets visible to them have unread messages."""
    def get(self, request, structure_slug, *args, **kwargs):
        """
        Checks the open tickets visible to the user for unread messages.

        Only messages sent by users are checked.

        Raises PermissionDenied if the user is not an operator of the structure.

        Args:
            request: The current HttpRequest.

        Returns:
            A Response whose "count" key is a boolean, as returned by
            TicketReply.get_unread_messages_count.
        """
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
