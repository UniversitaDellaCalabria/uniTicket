from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .models import ChatMessageModel
from rest_framework.serializers import ModelSerializer, CharField


class ChatMessageModelSerializer(ModelSerializer):
    user = CharField(source='user.pk', read_only=True)
    recipient = CharField(source='recipient.pk')

    def create(self, validated_data):
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
    class Meta:
        model = get_user_model()
        fields = ('pk',)
