from copy import deepcopy
import json
import logging

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core import serializers
from django.core.exceptions import BadRequest
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404

from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, viewsets

from uni_ticket.dynamic_form import serialize_form
from uni_ticket.models import Ticket, TicketAssignment, TicketCategory, TicketReply
from uni_ticket.views.user import TicketAddNew, TicketClose, TicketDetail
from uni_ticket.settings import TICKET_CREATE_BUTTON_NAME
from uni_ticket.utils import user_is_manager, user_is_operator, visible_tickets_to_user

from organizational_area.models import OrganizationalStructure
from api_rest.authorizations import AuthorizationToken


from .. serializers import (
    GroupSerializer,
    OrganizationalStructureSerializer,
    TicketCategorySerializer,
    TicketSerializer,
    UserSerializer
)

logger = logging.getLogger(__name__)


# ViewSets define the view behavior.
class UserViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAdminUser]
    queryset = get_user_model().objects.all()
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    permission_classes = [permissions.IsAdminUser]
    queryset = Group.objects.all()
    serializer_class = GroupSerializer


class uniTicketROGenericList(generics.ListAPIView):
    # authentication_classes = [AuthorizationToken, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]


def message_level(level:int):
    levels = {v:k for k,v in messages.DEFAULT_LEVELS.items()}
    return levels.get(level, level)


class TicketAPIBaseView(APIView):
    """
        base class to port in the API all the legacy code
    """

    # TODO: AgID MoDI also here?
    # authentication_classes = [
        # AuthorizationToken, SessionAuthentication
    # ]
    permission_classes = [permissions.IsAuthenticated]

    def get_messages(self):
        return [
            {
                message_level(i.level): i.message
                for i in messages.get_messages(self.request)
            }
        ]


class TicketAPIStruttureList(uniTicketROGenericList):
    queryset = OrganizationalStructure.objects.filter(is_active=True)
    lookup_field = 'pk'
    serializer_class = OrganizationalStructureSerializer


class TicketAPITicketCategoryList(uniTicketROGenericList):
    queryset = TicketCategory.objects.filter(is_active=True)
    lookup_field = 'pk'
    serializer_class = TicketCategorySerializer
