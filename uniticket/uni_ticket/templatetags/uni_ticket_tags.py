import inspect
import markdown as md
import os
import re

from django import template
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.template.defaultfilters import stringfilter

from django_form_builder import dynamic_fields
from uni_ticket.models import TicketCategory, TicketCategoryCondition
from uni_ticket import settings as uni_ticket_settings
from uni_ticket.utils import (
    format_slugged_name,
    get_user_type,
    user_is_in_default_office,
    user_is_operator,
    user_manage_something,
)

register = template.Library()


@register.simple_tag
def not_a_simple_user(user):
    """Returns True if the user is a manager or an operator in some structure."""
    return user_manage_something(user)


@register.filter
def filename(value):
    """
    Returns the base name of an attachment file.

    Returns:
        The file name, or a "resource no longer available" message if the
        file does not exist on disk.
    """
    if os.path.exists(value.path):
        return os.path.basename(value.file.name)
    return _("Risorsa non più disponibile")


@register.filter
def no_slugged(value):
    """Returns the slugged value formatted as a human readable name."""
    return format_slugged_name(value)


@register.simple_tag
def year_list():
    """Returns the range of years from 2019 to the current one."""
    return range(2019, timezone.localdate().year + 1)


@register.simple_tag
def categories_list(structure, user):
    """
    Returns the categories of the structure the user can manage.

    Users in the default office get all the structure categories, the other
    operators only the categories of their offices.

    Args:
        structure: The organizational structure.
        user: The current user.

    Returns:
        A queryset or a list of categories.
    """
    if user_is_in_default_office(user, structure):
        return TicketCategory.objects.filter(organizational_structure=structure)
    categories = []
    employee_offices = user_is_operator(user, structure)
    for eo in employee_offices:
        office_categories = TicketCategory.objects.filter(
            organizational_office=eo.office
        )
        for oc in office_categories:
            categories.append(oc)
    return categories


@register.simple_tag
def current_date():
    """Returns the current local date."""
    return timezone.localtime().date()


# @register.simple_tag
# def conditions_in_category(category):
    # conditions = TicketCategoryCondition.objects.filter(
        # category=category, is_active=True
    # ).count()
    # return conditions


# @register.simple_tag
# def tasks_in_category(category):
    # tasks = category.get_tasks().count()
    # return tasks


@register.simple_tag
def simple_user_context_name():
    """Returns the context name used for simple users."""
    return uni_ticket_settings.CONTEXT_SIMPLE_USER


@register.simple_tag
def get_usertype(user, structure, label_value_tuple=False):
    """
    Returns the management URL prefix of the user type in the structure.

    Args:
        user: The current user.
        structure: The organizational structure.
        label_value_tuple: If True, returns a (label, value) tuple.

    Returns:
        The URL prefix, or a (user type, URL prefix) tuple.
    """
    label = get_user_type(user, structure)
    value = uni_ticket_settings.MANAGEMENT_URL_PREFIX[label]
    if label_value_tuple:
        return (label, value)
    return value


@register.simple_tag
def get_label_from_form(form, field_name):
    """
    Returns the label and pre_text of a form field.

    If the field does not exist, the name is treated as a formset field
    (``<parent>-0-<column>``) and only the parent field pre_text is returned
    when the column matches its first choice.

    Args:
        form: The form.
        field_name: Name of the field (or of a formset sub-field).

    Returns:
        A (label, pre_text) tuple, or False if no field matches.
    """
    field = form.fields.get(field_name)
    if field:
        return (field.label, getattr(field, "pre_text", False))
    # return False

    # formset (we need the parent field label)
    formset_field_name_parts = field_name.rsplit("-0-", 1)
    # parent formset field
    field = form.fields.get(formset_field_name_parts[0])
    if field:
        # toDo: better reference to django_form_builder for regex and methods
        _regexp = "(?P<colname>[a-zA-Z0-9_ ]*)"
        content = re.search(
            _regexp, field.choices[0]) if field.choices else False
        ###
        if content and content.groupdict()["colname"] == formset_field_name_parts[1]:
            # get formset field pre_text
            return (False, getattr(field, "pre_text", False))
    return False


@register.filter
def get_dyn_field_name(value):
    """
    Returns the field_type of the django_form_builder field class with the given name.

    Returns:
        The field type, or the value itself if no class matches.
    """
    for m in inspect.getmembers(dynamic_fields, inspect.isclass):
        if m[0] == value:
            return getattr(m[1], "field_type")
    return value


@register.simple_tag
def user_from_pk(user_id):
    """
    Returns the user with the given pk.

    Returns:
        The user, or False if user_id is empty.
    """
    if not user_id:
        return False
    user_model = get_user_model()
    user = user_model.objects.get(pk=user_id)
    if not user:
        return False
    return user


@register.simple_tag
def user_operator_chat(user, structure):
    """Returns True if the user can chat as operator (employee of the structure default office)."""
    return user_is_in_default_office(user, structure)


@register.simple_tag
def uni_ticket_settings_value(name, **kwargs):
    """
    Returns the value of an uni_ticket setting.

    If kwargs are given, the value is formatted with them.

    Args:
        name: Setting name.

    Returns:
        The setting value, or None if it does not exist.
    """
    value = getattr(uni_ticket_settings, name, None)
    if value and kwargs:
        return value.format(**kwargs)
    return value


@register.simple_tag
def obj_get_attr(obj, attr, **kwargs):
    """Returns the attribute of an object, or the key of a dict (None if missing)."""
    if type(obj) == dict: return obj.get(attr, None)
    return getattr(obj, attr, None)


@register.filter()
@stringfilter
def markdown(value):
    """Renders a markdown string to HTML with the configured extensions."""
    return md.markdown(value, extensions=uni_ticket_settings.MARKDOWN_EXTENSIONS)


@register.simple_tag
def ticket_has_been_taken(ticket, user=None, structure=None, exclude_readonly=False):
    """Returns True if the ticket has been taken (see Ticket.has_been_taken)."""
    return ticket.has_been_taken(
        user=user, structure=structure, exclude_readonly=exclude_readonly
    )


@register.simple_tag
def ticket_is_open(ticket, user=None):
    """Returns True if the ticket is open (see Ticket.is_open)."""
    return ticket.is_open(user)


@register.simple_tag
def app_is_installed(name):
    """Returns True if the app is in INSTALLED_APPS."""
    return name in settings.INSTALLED_APPS


@register.simple_tag
def ticket_can_be_deleted(ticket, ticket_taken, ticket_assignments, user):
    """
    Returns True if the user can delete the ticket.

    The user must be the creator, and the ticket must not be compiled by
    another user, protocolled, closed, taken or assigned to more than one office.

    Args:
        ticket: The ticket.
        ticket_taken: True if the ticket has been taken.
        ticket_assignments: The ticket assignments queryset.
        user: The current user.
    """
    if ticket.created_by != user: return False
    if ticket.compiled_by: return False
    if ticket.protocol_number: return False
    if ticket.protocol_nrecord: return False
    if ticket.is_closed: return False
    if ticket_taken: return False
    if ticket_assignments.count() > 1: return False
    return True

@register.simple_tag
def ticket_can_be_edited(ticket, ticket_taken, user):
    """
    Returns True if the user can edit the ticket.

    The user must be the creator, and the ticket must not be protocolled,
    closed or taken.

    Args:
        ticket: The ticket.
        ticket_taken: True if the ticket has been taken.
        user: The current user.
    """
    if ticket.created_by != user: return False
    if ticket.protocol_number: return False
    if ticket.protocol_nrecord: return False
    if ticket.is_closed: return False
    if ticket_taken: return False
    return True

@register.simple_tag
def ticket_can_be_closed_from_user(ticket, user):
    """
    Returns True if the user can close the ticket.

    The user must be the creator, the ticket must not be closed and, if it is a
    draft, it must have been compiled by another user.
    """
    if ticket.created_by != user: return False
    if ticket.draft:
        if not ticket.compiled_by: return False
        if ticket.created_by != user: return False
    if ticket.is_closed: return False
    return True