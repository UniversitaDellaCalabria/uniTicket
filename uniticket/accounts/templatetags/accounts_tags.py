from django import template

from accounts import settings


register = template.Library()


@register.simple_tag
def accounts_settings_value(name, **kwargs):
    value = getattr(settings, name, None)
    if value and kwargs:
        return value.format(**kwargs)
    return value
