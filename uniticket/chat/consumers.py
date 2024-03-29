import json
import logging

from django.contrib.auth import get_user_model
from django.utils.timezone import now

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from datetime import timedelta

from chat.settings import SECONDS_TO_KEEP_ALIVE

from . models import UserChannel
from . utils import chat_operator


logger = logging.getLogger(__name__)


class ChatConsumer(WebsocketConsumer):

    def _create_user_channel(self, user, channel_name, room):
        # purge old user channels in room
        UserChannel.objects.filter(user=user, room=room).delete()
        # create new
        UserChannel.objects.create(user=user,
                                   channel=channel_name,
                                   room=room)

    def _purge_inactive_channels(self):
        stored_channels = UserChannel.objects.filter(room=self.room_name).exclude(user=self.user)
        for sc in stored_channels:
            if sc.last_seen < now() - timedelta(seconds=SECONDS_TO_KEEP_ALIVE):
                UserChannel.objects.get(channel=sc.channel).delete()

    def _check_user_is_active(self, user):
        return UserChannel.objects.filter(user=user,
                                          room=self.room_name).first()

    def _notify_other_users(self):
        # Send message to room group
        notification = {
            'type': 'join_room',
            'room': self.room_name,
            'user': self.user.pk,
            # 'is_operator': chat_operator(self.user, self.room_name),
            'user_fullname': '{} {}'.format(self.user.first_name,
                                            self.user.last_name)
        }
        logger.info("connect notification: {}".format(notification))
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            notification
        )

    def _add_users_in_frontend(self):
        active_users = UserChannel.objects.filter(room=self.room_name).exclude(user=self.user)
        for au in active_users:
            if(chat_operator(self.user, self.room_name)) or (chat_operator(au.user, self.room_name)):
                notification = {
                    'type': 'add_user',
                    'room': self.room_name,
                    'user': au.user.pk,
                    'operator_status': au.status,
                    # 'is_operator': chat_operator(au.user, self.room_name),
                    'user_fullname': '{} {}'.format(au.user.first_name,
                                                    au.user.last_name)
                }
                async_to_sync(self.channel_layer.send)(
                    self.channel_name,
                    notification
                )

    def connect(self):
        user_id = self.scope["session"]["_auth_user_id"]

        # only for logged users
        if not user_id: self.close()

        self.user = get_user_model().objects.get(pk=user_id)

        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.group_name = self.room_name

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

        # Create a new UserChannel and purge older
        self._create_user_channel(user=self.user,
                                  channel_name=self.channel_name,
                                  room=self.room_name)
        logger.info("{} connected to websocket".format(self.user))
        self.accept()

        self._purge_inactive_channels()
        self._notify_other_users()
        self._add_users_in_frontend()

    def disconnect(self, close_code):
        logger.info("disconnected from websocket")
        UserChannel.objects.filter(channel=self.channel_name,
                                   room=self.room_name).delete()
        user_id = self.scope["session"]["_auth_user_id"]
        user = get_user_model().objects.get(pk=user_id)

        # Send message to room group
        notification = {
            'type': 'leave_room',
            'room': self.room_name,
            'user': self.user.pk,
            'user_fullname': '{} {}'.format(self.user.first_name,
                                            self.user.last_name)
        }
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            notification
        )

        # Leave room group
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name,
            self.channel_name
        )

    # Join a room
    def join_room(self, event):
        user = get_user_model().objects.filter(pk=event['user']).first()
        if chat_operator(self.user, event['room']) or \
           (user and event['user'] != self.user.pk and
           chat_operator(user, event['room'])):
            self.send(
                text_data=json.dumps({
                    'command': 'join_room',
                    'room': event['room'],
                    'user': event['user'],
                    'is_operator': chat_operator(user, event['room']),
                    'user_fullname': '{} {}'.format(user.first_name,
                                                    user.last_name)
                })
            )

    # Leave a room
    def leave_room(self, event):
        self.send(
            text_data=json.dumps({
                'command': 'leave_room',
                'room': event['room'],
                'user': event['user'],
            })
        )

    # Add user to room
    def add_user(self, event):
        user = get_user_model().objects.filter(pk=event['user']).first()
        self.send(
            text_data=json.dumps({
                'command': 'add_user',
                'room': event['room'],
                'user': event['user'],
                'is_operator': chat_operator(user, self.room_name),
                'operator_status': event['operator_status'],
                'user_fullname': event['user_fullname'],
            })
        )

    # Receive one-to-one message from WebSocket
    def receive(self, event):
        self.send(
            text_data=json.dumps({
                'message': event['message'],
                'user_fullname': event['user_fullname'],
                'is_operator': event['is_operator'],
                'operator_status': event['operator_status'],
            })
        )

    # Receive message in room
    def receive_group_message(self, event):
        # broadcast only for staff users
        message = event['message']
        user_fullname = event['user_fullname']
        # Send message to WebSocket
        self.send(
            text_data=json.dumps({
                'message': message,
                'user_fullname': user_fullname,
                'is_operator': event['is_operator'],
                'operator_status': event['operator_status'],
            })
        )

    # Room operator changed status
    def operator_status_changed(self, event):
        # broadcast only for staff users
        user = event['user']
        status = event['status']
        # Send message to WebSocket
        self.send(
            text_data=json.dumps({
                'command': 'update_operator_status',
                'status': status,
                'user': user
            })
        )
