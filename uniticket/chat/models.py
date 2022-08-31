import logging

from django.contrib.auth import get_user_model
from django.db.models import (Model,
                              CharField,
                              BooleanField,
                              TextField,
                              DateTimeField,
                              ForeignKey,
                              CASCADE)
from django.utils.html import strip_tags

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from uni_ticket.utils import get_text_with_hrefs

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

    def notify_single_client(self, sender, recipient):
        """
        Inform client there is a new message.
        """
        channel_layer = get_channel_layer()
        sender_channel = UserChannel.objects.filter(user__pk=sender.pk,
                                                    room=self.room).first()
        recipient_channel = UserChannel.objects.filter(user__pk=recipient.pk,
                                                       room=self.room).first()

        notification = {
            'type': 'receive',
            'message': self.id,
            'user_fullname': '{} {}'.format(self.user.first_name,
                                            self.user.last_name),
            'is_operator': chat_operator(self.user, self.room),
            'operator_status': sender_channel.status if sender_channel else True
        }

        # print(notification)

        if sender_channel and sender_channel.channel:
            async_to_sync(channel_layer.send)(sender_channel.channel,
                                              notification)

        if recipient_channel and recipient_channel.channel:
            async_to_sync(channel_layer.send)(recipient_channel.channel,
                                              notification)

    def notify_ws_clients(self):
        """
        Inform client there is a new message.
        """
        channel_layer = get_channel_layer()
        sender_channel = UserChannel.objects.filter(user=self.user,
                                                    room=self.room).first()
        notification = {
            'type': 'receive_group_message',
            'message': '{}'.format(self.id),
            'user_fullname': '{} {}'.format(self.user.first_name,
                                            self.user.last_name),

            'is_operator': chat_operator(self.user, self.room),
            'operator_status': sender_channel.status if sender_channel else True
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
        # Escape text to avoi XSS attack and render hrefs
        self.body = get_text_with_hrefs(strip_tags(self.body))
        super(ChatMessageModel, self).save(*args, **kwargs)
        channel = UserChannel.objects.filter(user=self.user,
                                             room=self.room).first()
        if channel:
            channel.save(update_fields=['last_seen'])
        if not new:
            if self.broadcast: self.notify_ws_clients()
            else:
                # notify sender and recipient
                self.notify_single_client(sender=self.user,
                                          recipient=self.recipient)
                # notify sender
                # self.notify_single_client(recipient=self.user)

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
    status = BooleanField(default=True)

    def change_status(self):
        self.status = not self.status
        self.save(update_fields=['status'])

        # Inform client there is a new message.
        notification = {
            'type': 'operator_status_changed',
            'user': self.user.pk,
            'status': self.status
        }
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(self.room,
                                                notification)

    # Meta

    class Meta:
        verbose_name = 'Canale Utente'
        verbose_name_plural = 'Canali Utenti'
        ordering = ('-created',)
