from django import template

from chat.utils import chat_operator_online


register = template.Library()


@register.simple_tag
def structure_operator_online(current_user, structure_slug):
    return chat_operator_online(current_user, structure_slug)
