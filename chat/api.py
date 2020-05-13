from django.conf import settings
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
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
    page_size = settings.MESSAGES_TO_LOAD


class ChatMessageModelViewSet(ModelViewSet):
    queryset = ChatMessageModel.objects.all()
    serializer_class = ChatMessageModelSerializer
    allowed_methods = ('GET', 'POST', 'HEAD', 'OPTIONS')
    authentication_classes = (CsrfExemptSessionAuthentication,)
    pagination_class = ChatMessagePagination

    def create(self, request):
        channel = UserChannel.objects.filter(user=request.user,
                                             room=request.POST['room']).first()
        if channel:
            channel.save(update_fields=['last_seen'])
        return super(ChatMessageModelViewSet, self).create(request)

    def list(self, request, *args, **kwargs):
        self.queryset = self.queryset.filter(Q(recipient=request.user) |
                                             Q(user=request.user))
        target = self.request.query_params.get('target', None)
        room_name = self.request.query_params.get('room', None)
        broadcast = self.request.query_params.get('broadcast', False)

        if room_name:
            self.queryset = self.queryset.filter(room=room_name)
            channel = UserChannel.objects.filter(user=request.user,
                                                 room=room_name).first()
            if channel:
                channel.save(update_fields=['last_seen'])
        if target and int(target)==request.user.pk:
            self.queryset = self.queryset.filter(user=request.user,
                                                 broadcast=True)
        elif target:
            self.queryset = self.queryset.filter(
                Q(recipient=request.user, user__pk=int(target)) |
                Q(recipient__pk=int(target), user=request.user))

        return super(ChatMessageModelViewSet, self).list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        room = self.request.query_params.get('room')
        msg = self.queryset.filter(Q(recipient=request.user) | Q(user=request.user),
                                   pk=kwargs['pk'],
                                   room=room).first()
        serializer = self.get_serializer(msg)
        return Response(serializer.data)


class UserModelViewSet(ModelViewSet):
    queryset = get_user_model().objects.all()
    serializer_class = UserModelSerializer
    allowed_methods = ('GET', 'HEAD', 'OPTIONS')
    pagination_class = None  # Get all user

    def list(self, request, *args, **kwargs):
        # Get all users except yourself
        self.queryset = self.queryset.exclude(id=request.user.id)
        return super(UserModelViewSet, self).list(request, *args, **kwargs)
