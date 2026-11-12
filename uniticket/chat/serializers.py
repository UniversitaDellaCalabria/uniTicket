from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .models import ChatMessageModel
from rest_framework.serializers import ModelSerializer, CharField


class ChatMessageModelSerializer(ModelSerializer):
    """Serializes a chat message, with the users as pks."""
    user = CharField(source='user.pk', read_only=True)
    recipient = CharField(source='recipient.pk')

    def create(self, validated_data):
        """
        Creates a message from the current user to the given recipient.

        Raises Http404 if the recipient does not exist.

        Returns:
            The saved ChatMessageModel.
        """
        user = self.context['request'].user
        room = self.validated_data['room']
        broadcast = self.validated_data['broadcast']

        recipient = get_object_or_404(get_user_model(),
                                      pk=validated_data['recipient']['pk'])

        msg = ChatMessageModel(recipient=recipient,
                               room=room,
                               body=validated_data['body'],
                               user=user,
                               broadcast=broadcast)
        msg.save()
        return msg

    class Meta:
        model = ChatMessageModel
        fields = ('id', 'user', 'recipient', 'room', 'created', 'body', 'broadcast')


class UserModelSerializer(ModelSerializer):
    """Serializes a user as its pk."""
    class Meta:
        model = get_user_model()
        fields = ('pk',)
