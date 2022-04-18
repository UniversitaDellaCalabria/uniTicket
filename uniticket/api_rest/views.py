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

from rest_framework.authentication import SessionAuthentication
from rest_framework.exceptions import PermissionDenied
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, viewsets

from uni_ticket.dynamic_form import serialize_form
from uni_ticket.models import Ticket, TicketCategory, TicketReply
from uni_ticket.views.user import TicketAddNew, TicketClose, TicketDetail
from uni_ticket.settings import TICKET_CREATE_BUTTON_NAME
from organizational_area.models import OrganizationalStructure
from api_rest.authorizations import AuthorizationToken
from uni_ticket.forms import OrganizationalStructureAlertForm


from . serializers import (
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
    authentication_classes = [AuthorizationToken, SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]

def message_level(level:int):
    levels = {v:k for k,v in messages.DEFAULT_LEVELS.items()}
    return levels.get(level, level)


class TicketAPIBaseView(APIView):
    """
        base class to port in the API all the legacy code
    """

    # TODO: AgID MoDI also here?
    authentication_classes = [
        AuthorizationToken, SessionAuthentication
    ]
    permission_classes = [permissions.IsAuthenticated]

    def get_messages(self):
        return [
            {
                message_level(i.level): i.message 
                for i in messages.get_messages(self.request)
            }
        ]


class TicketAPIView(TicketAPIBaseView):
    """
    Creates a new ticket.

    self.legacy_view.title is a TicketCategory object that checks the permissions
    over the request object.

        - allow_anonymous
        - allow_employee
        - allow_guest
        - allow_user
        - allowed_to_user
        - allowed_users
    """

    def build_response(self) -> dict:
        """
        returns the dictionary for the JSON response
        """
        _messages = self.get_messages()
        return(
            dict(
                # We may do it but ... it's crazy! :-)
                # uniticket_html_page = legacy_response.content,
                name = self.legacy_view.title.name,
                description = self.legacy_view.title.description,
                protocol_required = self.legacy_view.title.protocol_required,
                slug = self.legacy_view.title.slug,
                messages = _messages,
                conditions = json.loads(
                    serializers.serialize(
                        'json', self.legacy_view.title.ticketcategorycondition_set.all()
                    )
                ),
                form = serialize_form(self.legacy_view.form)
            )
        )

    def dispatch(self, request, *args, **kwargs):
        self.legacy_view = TicketAddNew()
        self.legacy_view.request = request
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, structure_slug, category_slug):
        """
        Return a ticket by structure_slug, category_slug
        """
        legacy_response = self.legacy_view.get(request, structure_slug, category_slug)
        if legacy_response.status_code == 302:
            raise PermissionDenied(
                {
                    "redirect_url": legacy_response.url,
                    "messages": self.get_messages()
                }
            )
        if legacy_response.status_code != 200:
            raise PermissionDenied()
        return Response(self.build_response())

    def post(self, request, structure_slug, category_slug):
        """
        Return a ticket by structure_slug, category_slug
        """
        # useless ... untill you don't except csrf on the legacy view ... but no.
        # request._set_post(request.data)
        request.api_data = deepcopy(request.data)
        request.api_data[TICKET_CREATE_BUTTON_NAME] = 1
        legacy_response = self.legacy_view.post(request, structure_slug, category_slug)
        logger.debug(legacy_response)
        if self.legacy_view.form.errors:
            return Response(self.build_response())

        elif getattr(self.legacy_view, 'ticket_assignment', None):
            _res = self.build_response()
            _res['compiled_form'] = self.legacy_view.form.cleaned_data
            _res['status'] = {
                k: getattr(self.legacy_view.ticket, k)
                for k in ("code", "created", "is_closed", "protocol_number", "protocol_date")
            }
            _res['status']["created_by"] = self.legacy_view.ticket.created_by.__str__()
            # _res['assigned'] = self.legacy_view.ticket_assignment.__str__()
            return Response(_res)

        else:
            raise BadRequest()


class TicketAPIStruttureList(uniTicketROGenericList):
    queryset = OrganizationalStructure.objects.filter(is_active=True)
    lookup_field = 'pk'
    serializer_class = OrganizationalStructureSerializer


class TicketAPITicketCategoryList(uniTicketROGenericList):
    queryset = TicketCategory.objects.filter(is_active=True)
    lookup_field = 'pk'
    serializer_class = TicketCategorySerializer
    


class TicketAPIDetail(TicketAPIBaseView):
    """
    Shows the status of a Ticket
    """

    def dispatch(self, request, *args, **kwargs):
        self.legacy_view = TicketDetail()
        self.legacy_view.request = request
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, ticket_uid):
        """
        Return a ticket by structure_slug, category_slug
        """
        legacy_response = self.legacy_view.get(request, ticket_uid, api=True)
        if isinstance(legacy_response, dict):
            data = self.legacy_view.data
            for i in (
                "ticket_assignments",
                'path_allegati',
                'details',
                "ticket_form",
                "logs",
                "ticket_task"
            ):
                data.pop(i)

            ticket = data.pop("ticket")
            _messages = TicketReply.objects.filter(ticket=ticket)
            data["ticket"] = ticket.serialize()
            data["messages"] = [i.serialize() for i in _messages if i]
            return Response(data)
        if legacy_response.status_code == 404:
            raise Http404()
        if legacy_response.status_code != 200:
            raise PermissionDenied()
        else:
            raise BadRequest()


class TicketAPIListCreated(uniTicketROGenericList):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer

    def list(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            raise PermissionDenied()

        queryset = self.filter_queryset(
            Ticket.objects.filter(
                Q(created_by=request.user) | Q(compiled_by=request.user)
            )
        )

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class TicketAPIClose(TicketAPIBaseView):

    def build_response(self) -> dict:
        """
        returns the dictionary for the JSON response
        """
        return(
            dict(
                messages = self.get_messages(),
                ticket = self.legacy_view.context_data['sub_title'].serialize(),
                form = serialize_form(self.legacy_view.form)
            )
        )

    def dispatch(self, request, *args, **kwargs):
        self.legacy_view = TicketClose()
        self.legacy_view.request = request
        self.user = request.user
        return super().dispatch(request, *args, **kwargs)

    def close(self, request, ticket_id, *args, **kwargs):
        request.api_data = getattr(request, "data", {})
        self.legacy_view.dispatch(
            request, ticket_id=ticket_id
        )
        legacy_response = self.legacy_view.post(
            request
        )
        logger.debug(legacy_response)
        return Response(self.build_response())
    
    def get(self, request, ticket_id, *args, **kwargs):
        return self.close(request, ticket_id, *args, **kwargs)

    def post(self, request, ticket_id, *args, **kwargs):
        return self.close(request, ticket_id, *args, **kwargs)