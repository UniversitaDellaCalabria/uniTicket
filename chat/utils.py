from organizational_area.models import OrganizationalStructure
from uni_ticket.utils import user_is_in_default_office


def chat_operator(user, structure_slug):
    if not structure_slug: return False
    if not user: return False
    structure = OrganizationalStructure.objects.filter(slug=structure_slug,
                                                       is_active=True).first()
    if not structure: return False
    return user_is_in_default_office(user, structure)
