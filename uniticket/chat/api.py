from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from chat.settings import MESSAGES_TO_LOAD

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
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
        return


class ChatMessagePagination(PageNumberPagination):
    """
    Limit message prefetch to one page.
    """
    page_size = MESSAGES_TO_LOAD


class ChatMessageModelViewSet(ModelViewSet):
    queryset = ChatMessageModel.objects.all()
    serializer_class = ChatMessageModelSerializer
    allowed_methods = ('GET', 'POST', 'HEAD', 'OPTIONS')
    authentication_classes = (CsrfExemptSessionAuthentication,)
    pagination_class = ChatMessagePagination

    def list(self, request, *args, **kwargs):
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


class UserModelViewSet(ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserModelSerializer
    allowed_methods = ('PUT',)
    authentication_classes = (CsrfExemptSessionAuthentication,)
    pagination_class = None  # Get all user

    def retrieve(self, request, *args, **kwargs):
        try:
            if not request.user.is_superuser and int(kwargs.get('pk')) != request.user.pk:
                return Response(_("Non hai accesso a questa risorsa"))
        except ValueError:
            return Response(_("Argomenti errati"))
        user = self.queryset.filter(pk=kwargs.get('pk')).first()
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        if not request.user.is_superuser and int(kwargs.get('pk')) != request.user.pk:
            return Response(_("Non hai accesso a questa risorsa"))
        channel = UserChannel.objects.filter(room=request.POST['room'],
                                             user__pk=kwargs.get('pk')).first()
        if channel:
            channel.change_status()
        return Response("updated")
