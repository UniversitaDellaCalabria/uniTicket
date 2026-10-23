from django import template
from django.contrib.auth.models import Group

register = template.Library()


@register.filter(name='has_group')
def has_group(user, group_name):
    """Check if a user belongs to a group.

    Args:
        user: The user to check.
        group_name: The name of the group.

    Returns:
        True if the group exists and the user is a member, else False.
    """
    if not user or not group_name: return False
    group = Group.objects.filter(name=group_name).first()
    if not group: return False
    return group in user.groups.all()
