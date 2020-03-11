from django.apps import apps

from organizational_area.models import OrganizationalStructure
from uni_ticket.utils import user_is_in_default_office


def chat_operator(user, structure_slug):
    if not structure_slug: return False
    if not user: return False
    structure = OrganizationalStructure.objects.filter(slug=structure_slug,
                                                       is_active=True).first()
    if not structure: return False
    return user_is_in_default_office(user, structure)

def chat_operator_online(user, structure_slug):
    user_channel = apps.get_model('chat', 'UserChannel')
    users_in_room = user_channel.objects.filter(room=structure_slug).exclude(user=user)
    structure = OrganizationalStructure.objects.filter(slug=structure_slug,
                                                       is_active=True).first()
    if not structure: return False
    for room_user in users_in_room:
        if user_is_in_default_office(room_user.user, structure):
            return True
    return False
