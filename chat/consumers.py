from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
import logging

from . models import UserChannel
from . utils import chat_operator


logger = logging.getLogger(__name__)


class ChatConsumer(WebsocketConsumer):

    def _create_user_channel(self, user, channel_name, room):
        # purge old user channels in room
        UserChannel.objects.filter(user=user, room=room).delete()
        # create new
        UserChannel.objects.create(user=user,
                                   channel=self.channel_name,
                                   room=room)

    def connect(self):
        user_id = self.scope["session"]["_auth_user_id"]

        # only for logged users
        if not user_id: self.close()

        self.user = get_user_model().objects.get(pk=user_id)

        # self.group_name = "{}".format(user_id)
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.group_name = 'chat_{}'.format(self.room_name)

        # Join room group
        async_to_sync(self.channel_layer.group_add)(
            self.group_name,
            self.channel_name
        )

        self._create_user_channel(user=self.user,
                                  channel_name=self.channel_name,
                                  room=self.room_name)
        logger.info("{} connected to websocket".format(self.user))
        self.accept()

        # Send message to room group
        notification = {
            'type': 'join_room',
            'room': self.room_name,
            'user': self.user.username,
            'user_fullname': '{} {}'.format(self.user.first_name,
                                            self.user.last_name)
        }
        logger.info("connect notification: {}".format(notification))
        async_to_sync(self.channel_layer.group_send)(
            self.group_name,
            notification
        )

        active_users = UserChannel.objects.filter(room=self.room_name).exclude(user=self.user)
        for au in active_users:
            if(chat_operator(self.user, self.room_name)) or (chat_operator(au.user, self.room_name)):
                notification = {
                    'type': 'add_user',
                    'room': self.room_name,
                    'user': au.user.username,
                    'user_fullname': '{} {}'.format(au.user.first_name,
                                                    au.user.last_name)
                }
                async_to_sync(self.channel_layer.send)(
                    self.channel_name,
                    notification
                )

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
            'user': self.user.username,
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
        user = get_user_model().objects.filter(username=event['user']).first()
        if chat_operator(self.user, event['room']) or (user and event['user'] != self.user.username and chat_operator(user, event['room'])):
            self.send(
                text_data=json.dumps({
                    'command': 'join_room',
                    'room': event['room'],
                    'user': event['user'],
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
        self.send(
            text_data=json.dumps({
                'command': 'add_user',
                'room': event['room'],
                'user': event['user'],
                'user_fullname': event['user_fullname'],
            })
        )

    # Receive one-to-one message from WebSocket
    def receive(self, event):
        message = event['message']
        user_fullname = event['user_fullname']
        logger.info(message)
        self.send(
            text_data=json.dumps({
                'message': message,
                'user_fullname': user_fullname
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
                'user_fullname': user_fullname
            })
        )
