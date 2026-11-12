from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from chat.settings import MESSAGES_TO_LOAD

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework.authentication import SessionAuthentication


from .serializers import ChatMessageModelSerializer, UserModelSerializer
from .models import ChatMessageModel, UserChannel


class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    SessionAuthentication scheme used by DRF. DRF's SessionAuthentication uses
    Django's session framework for authentication which requires CSRF to be
    checked. In this case we are going to disable CSRF tokens for the API.
    """

    def enforce_csrf(self, request):
        """Skips the CSRF check."""
        return


class ChatMessagePagination(PageNumberPagination):
    """
    Limit message prefetch to one page.
    """
    page_size = MESSAGES_TO_LOAD


class ChatMessageModelViewSet(CreateModelMixin,
                              ListModelMixin,
                              RetrieveModelMixin,
                              GenericViewSet):
    """
    API endpoint for the chat messages of the current user.

    Only list, retrieve and create are exposed: messages cannot be
    updated or deleted through the API.
    """
    queryset = ChatMessageModel.objects.all()
    serializer_class = ChatMessageModelSerializer
    authentication_classes = (CsrfExemptSessionAuthentication,)
    pagination_class = ChatMessagePagination

    def list(self, request, *args, **kwargs):
        """
        Lists the messages sent or received by the current user.

        The "room" query param filters by room and updates last_seen of the
        user channel in that room. The "target" query param (a user pk) keeps
        the messages exchanged with that user or, if it is the current user,
        their broadcast messages.

        Args:
            request: The current HttpRequest.

        Returns:
            A paginated Response, or an error message if target is not a number.
        """
        self.queryset = self.queryset.filter(Q(recipient=request.user) |
                                             Q(user=request.user))
        target = self.request.query_params.get('target', None)
        room_name = self.request.query_params.get('room', None)
        self.request.query_params.get('broadcast', False)

        if room_name:
            self.queryset = self.queryset.filter(room=room_name)
            channel = UserChannel.objects.filter(user=request.user,
                                                 room=room_name).first()
            if channel:
                channel.save(update_fields=['last_seen'])
        try:
            if target and int(target) == request.user.pk:
                self.queryset = self.queryset.filter(user=request.user,
                                                     broadcast=True)
            elif target:
                self.queryset = self.queryset.filter(
                    Q(recipient=request.user, user__pk=int(target)) |
                    Q(recipient__pk=int(target), user=request.user))

            return super(ChatMessageModelViewSet, self).list(request, *args, **kwargs)
        except ValueError:
            return Response(_("Argomenti errati"))

    def retrieve(self, request, *args, **kwargs):
        """
        Returns a message of the current user in the "room" query param room.

        If the message exists, updates last_seen of the user channel in the room.

        Args:
            request: The current HttpRequest.

        Returns:
            A Response with the serialized message.
        """
        room = self.request.query_params.get('room')
        msg = self.queryset.filter(Q(recipient=request.user) | Q(user=request.user),
                                   pk=kwargs['pk'],
                                   room=room).first()
        channel = UserChannel.objects.filter(user=request.user,
                                             room=room).first()
        if msg and channel:
            channel.save(update_fields=['last_seen'])
        serializer = self.get_serializer(msg)
        return Response(serializer.data)


class UserModelViewSet(GenericViewSet):
    """
    API endpoint to read a user and toggle their chat status.

    Only retrieve (GET) and update (PUT) are exposed: users cannot be
    listed, created, partially updated or deleted through the API.
    """
    queryset = get_user_model().objects.all()
    serializer_class = UserModelSerializer
    authentication_classes = (CsrfExemptSessionAuthentication,)

    def retrieve(self, request, *args, **kwargs):
        """
        Returns the requested user, if it is the current user or the current
        user is a superuser.

        Args:
            request: The current HttpRequest.

        Returns:
            A Response with the user pk, or an error message.
        """
        try:
            if not request.user.is_superuser and int(kwargs.get('pk')) != request.user.pk:
                return Response(_("Non hai accesso a questa risorsa"))
        except ValueError:
            return Response(_("Argomenti errati"))
        user = self.queryset.filter(pk=kwargs.get('pk')).first()
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        """
        Toggles the status of the user channel in the POSTed room.

        Allowed only on the current user, unless the current user is a superuser.

        Args:
            request: The current HttpRequest.

        Returns:
            A Response with "updated", or an error message.
        """
        if not request.user.is_superuser and int(kwargs.get('pk')) != request.user.pk:
            return Response(_("Non hai accesso a questa risorsa"))
        channel = UserChannel.objects.filter(room=request.POST['room'],
                                             user__pk=kwargs.get('pk')).first()
        if channel:
            channel.change_status()
        return Response("updated")
