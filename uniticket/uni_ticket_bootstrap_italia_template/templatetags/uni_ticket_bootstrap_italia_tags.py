from django import template
from django.conf import settings


register = template.Library()


@register.simple_tag
def is_list(value):
    """Returns True if the value is a list."""
    return isinstance(value, list)


@register.simple_tag
def settings_value(name, **kwargs):
    """
    Returns the value of a Django setting.

    If kwargs are given, the value is formatted with them.

    Args:
        name: Setting name.

    Returns:
        The setting value, or None if it does not exist.
    """
    value = getattr(settings, name, None)
    if value and kwargs:
        return value.format(**kwargs)
    return value
