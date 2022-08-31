from django import template

register = template.Library()


@register.simple_tag
def is_list(value):
    return isinstance(value, list)
