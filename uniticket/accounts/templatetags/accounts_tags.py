from django import template

from accounts import settings


register = template.Library()


@register.simple_tag
def accounts_settings_value(name, **kwargs):
    """Return an accounts setting by name.

    Args:
        name: The setting name (e.g. EDITABLE_FIELDS).
        **kwargs: Values for the {placeholders} of a string setting.

    Returns:
        The setting value, formatted with kwargs if given,
        or None if the setting does not exist.
    """
    value = getattr(settings, name, None)
    if value and kwargs:
        return value.format(**kwargs)
    return value
