from rest_framework import serializers
from accounts.models import User
from django.contrib.auth.models import Group

from uni_ticket.models import TicketCategory


# Serializers define the API representation.
class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ['username',
                  'first_name',
                  'last_name',
                  'email',
                  'is_active',
                  'is_staff']


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ['url', 'name']


class TicketCategorySerializer(serializers.ModelSerializer):
    organizational_structure = serializers.SlugRelatedField(
        read_only=True,
        slug_field='slug'
    )
    organizational_office = serializers.SlugRelatedField(
        read_only=True,
        slug_field='slug'
    )

    class Meta:
        model = TicketCategory
        lookup_field = 'pk'
        exclude = (
            "allowed_users",
            # "organizational_structure",
            # "organizational_office"
            "confirm_message_text"
        )
