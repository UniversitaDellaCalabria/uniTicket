from django import template

from organizational_area import settings
from organizational_area.models import OrganizationalStructureOfficeEmployee


register = template.Library()


@register.simple_tag
def employee_offices(user, structure=None):
    """
    Returns all user offices relationships
    """
    if not user: return None
    oe = OrganizationalStructureOfficeEmployee.objects.filter(employee=user)
    if structure:
        oe = oe.filter(office__organizational_structure=structure)
    return oe


@register.simple_tag
def organizational_area_settings_value(name, **kwargs):
    value = getattr(settings, name, None)
    if value and kwargs:
        return value.format(**kwargs)
    return value
