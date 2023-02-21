from django import template
from django.conf import settings


register = template.Library()


@register.simple_tag
def is_list(value):
    return isinstance(value, list)


@register.simple_tag
def settings_value(name, **kwargs):
    value = getattr(settings, name, None)
    if value and kwargs:
        return value.format(**kwargs)
    return value
