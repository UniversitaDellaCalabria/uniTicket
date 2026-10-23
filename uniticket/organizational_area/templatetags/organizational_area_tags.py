from django import template

from organizational_area import settings
from organizational_area.models import OrganizationalStructureOfficeEmployee


register = template.Library()


@register.simple_tag
def employee_offices(user, structure=None):
    """Return the employee-office relationships of a user.

    Args:
        user: The user whose offices are returned.
        structure: If given, only offices of this structure are returned.

    Returns:
        QuerySet of OrganizationalStructureOfficeEmployee,
        or None if user is empty.
    """
    if not user: return None
    oe = OrganizationalStructureOfficeEmployee.objects.filter(employee=user)
    if structure:
        oe = oe.filter(office__organizational_structure=structure)
    return oe


@register.simple_tag
def organizational_area_settings_value(name, **kwargs):
    """Return an organizational_area setting by name.

    Args:
        name: The setting name (e.g. DEFAULT_ORGANIZATIONAL_STRUCTURE_OFFICE).
        **kwargs: Values for the {placeholders} of a string setting.

    Returns:
        The setting value, formatted with kwargs if given,
        or None if the setting does not exist.
    """
    value = getattr(settings, name, None)
    if value and kwargs:
        return value.format(**kwargs)
    return value
