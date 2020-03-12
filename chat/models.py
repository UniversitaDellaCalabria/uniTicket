import logging

from django.contrib.auth import get_user_model
from django.db.models import (Model,
                              CharField,
                              BooleanField,
                              TextField,
                              DateTimeField,
                              ForeignKey,
                              CASCADE)

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from . utils import chat_operator

logger = logging.getLogger(__name__)


class ChatMessageModel(Model):
    """
    This class represents a chat message. It has a owner (user), timestamp and
    the message body.

    """
    user = ForeignKey(get_user_model(), on_delete=CASCADE,
                      verbose_name='user',
                      related_name='from_user', db_index=True)
    recipient = ForeignKey(get_user_model(), on_delete=CASCADE,
                           verbose_name='recipient',
                           related_name='to_user', db_index=True,
                           null=True, blank=True)
    created = DateTimeField(auto_now_add=True,
                            editable=False,
                            db_index=True)
    read_date = DateTimeField(editable=False, null=True, blank=True)
    room = CharField(max_length=150, null=True, blank=True)
    body = TextField('body')
    broadcast = BooleanField(default=False)

    def __str__(self):
        return str(self.id)

    def characters(self):
        """
        Toy function to count body characters.
        :return: body's char number
        """
        return len(self.body)

    def notify_single_client(self, recipient):
        """
        Inform client there is a new message.
        """
        # import pdb; pdb.set_trace()
        notification = {
            'type': 'receive',
            'message': '{}'.format(self.id),
            'user_fullname': '{} {}'.format(self.user.first_name,
                                            self.user.last_name)
        }
        channel_layer = get_channel_layer()
        uc = UserChannel.objects.filter(user__username=recipient.username,
                                        room=self.room).first()
        if uc and uc.channel:
            async_to_sync(channel_layer.send)(uc.channel, notification)

    def notify_ws_clients(self):
        """
        Inform client there is a new message.
        """
        notification = {
            'type': 'receive_group_message',
            'message': '{}'.format(self.id),
            'user_fullname': '{} {}'.format(self.user.first_name,
                                            self.user.last_name)
        }
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(self.room,
                                                notification)

    def save(self, *args, **kwargs):
        """
        Trims white spaces, saves the message and notifies the recipient via WS
        if the message is new.
        """
        # broadcast only for staff users
        if self.broadcast and not chat_operator(self.user, self.room):
            return False
        new = self.id
        self.body = self.body.strip()  # Trimming whitespaces from the body
        super(ChatMessageModel, self).save(*args, **kwargs)
        if not new:
            if self.broadcast: self.notify_ws_clients()
            else:
                # notify recipient
                self.notify_single_client(recipient=self.recipient)
                # notify sender
                self.notify_single_client(recipient=self.user)

    # Meta
    class Meta:
        app_label = 'chat'
        verbose_name = 'message'
        verbose_name_plural = 'messages'
        ordering = ('-created',)


class UserChannel(Model):
    """
    This class represents a chat message. It has a owner (user), timestamp and
    the message body.

    """
    user = ForeignKey(get_user_model(), on_delete=CASCADE,
                      verbose_name='user', db_index=True)
    channel = CharField(max_length=150)
    room = CharField(max_length=150, null=True, blank=True)
    created = DateTimeField(auto_now_add=True,
                            editable=False,
                            db_index=True)
    last_seen = DateTimeField(auto_now=True)

    # Meta
    class Meta:
        verbose_name = 'Canale Utente'
        verbose_name_plural = 'Canale Utenti'
        ordering = ('-created',)
