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
    """Counts the open tickets of a structure not yet taken, for its managers."""
    def get(self, request, structure_slug, *args, **kwargs):
        """
        Returns the number of open tickets of the structure not yet taken.

        Raises PermissionDenied if the user is not a manager of the structure.

        Args:
            request: The current HttpRequest.

        Returns:
            A Response with the "count" key.
        """
        structure = get_object_or_404(OrganizationalStructure, slug=structure_slug)
        if not user_is_manager(request.user, structure): raise PermissionDenied
        unassigned_tickets = TicketAssignment.get_ticket_per_structure(structure=structure,
                                                                       closed=False,
                                                                       taken=False)
        return Response({'count': unassigned_tickets.count()})


class TicketAPIOpenCounter(TicketAPIBaseView):
    """Counts the open tickets of a structure already taken, for its managers."""
    def get(self, request, structure_slug, *args, **kwargs):
        """
        Returns the number of open tickets of the structure already taken.

        Raises PermissionDenied if the user is not a manager of the structure.

        Args:
            request: The current HttpRequest.

        Returns:
            A Response with the "count" key.
        """
        structure = get_object_or_404(OrganizationalStructure, slug=structure_slug)
        if not user_is_manager(request.user, structure): raise PermissionDenied
        open_tickets = TicketAssignment.get_ticket_per_structure(structure=structure,
                                                                 closed=False,
                                                                 taken=True)
        return Response({'count': open_tickets.count()})


class TicketAPIMyOpenCounter(TicketAPIBaseView):
    """Counts the open tickets of a structure taken by the current manager."""
    def get(self, request, structure_slug, *args, **kwargs):
        """
        Returns the number of open tickets of the structure taken by the user.

        Raises PermissionDenied if the user is not a manager of the structure.

        Args:
            request: The current HttpRequest.

        Returns:
            A Response with the "count" key.
        """
        structure = get_object_or_404(OrganizationalStructure, slug=structure_slug)
        if not user_is_manager(request.user, structure): raise PermissionDenied
        my_open_tickets = TicketAssignment.get_ticket_per_structure(structure=structure,
                                                                    closed=False,
                                                                    taken=True,
                                                                    taken_by=request.user)
        return Response({'count': my_open_tickets.count()})


class TicketAPIMessagesCounter(TicketAPIBaseView):
    """Tells a manager whether the followed open tickets of a structure have unread messages."""
    def get(self, request, structure_slug, *args, **kwargs):
        """
        Checks the followed open tickets of the structure for unread messages.

        Only tickets assigned to active offices are checked, and only messages
        sent by users.

        Raises PermissionDenied if the user is not a manager of the structure.

        Args:
            request: The current HttpRequest.

        Returns:
            A Response whose "count" key is a boolean, as returned by
            TicketReply.get_unread_messages_count.
        """
        structure = get_object_or_404(OrganizationalStructure, slug=structure_slug)
        if not user_is_manager(request.user, structure): raise PermissionDenied
        ticket_ids = TicketAssignment.objects.filter(
            office__organizational_structure=structure,
            office__is_active=True,
            ticket__is_closed=False,
            follow=True
        ).values_list('ticket__pk', flat=True).distinct()
        messages = TicketReply.get_unread_messages_count(ticket_ids=ticket_ids)
        return Response({'count': messages})
