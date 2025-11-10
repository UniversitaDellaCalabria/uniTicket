from rest_framework import serializers
from accounts.models import User
from django.contrib.auth.models import Group

from uni_ticket.models import Ticket, TicketCategory
from organizational_area.models import OrganizationalStructure


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


class OrganizationalStructureSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrganizationalStructure
        fields = '__all__'


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
            "allowed_users_lists",
            "confirm_message_text"
        )


class TicketSerializer(serializers.ModelSerializer):
    created_by = serializers.SlugRelatedField(
        read_only=True,
        slug_field='last_name'
    )
    compiled_by = serializers.SlugRelatedField(
        read_only=True,
        slug_field='last_name'
    )
    closed_by = serializers.SlugRelatedField(
        read_only=True,
        slug_field='last_name'
    )

    class Meta:
        model = Ticket
        lookup_field = 'pk'
        exclude = (
            "input_module",
        )
