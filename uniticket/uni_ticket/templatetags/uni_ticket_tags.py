import inspect
import markdown as md
import os
import re

from django import template
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext as _
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
    return user_manage_something(user)


@register.filter
def filename(value):
    if os.path.exists(value.path):
        return os.path.basename(value.file.name)
    return _("Risorsa non più disponibile")


@register.filter
def no_slugged(value):
    return format_slugged_name(value)


@register.simple_tag
def year_list():
    return range(2019, timezone.localdate().year + 1)


@register.simple_tag
def categories_list(structure, user):
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
    return timezone.localtime().date()


@register.simple_tag
def conditions_in_category(category):
    conditions = TicketCategoryCondition.objects.filter(
        category=category, is_active=True
    ).count()
    return conditions


@register.simple_tag
def tasks_in_category(category):
    tasks = category.get_tasks().count()
    return tasks


@register.simple_tag
def simple_user_context_name():
    return uni_ticket_settings.CONTEXT_SIMPLE_USER


@register.simple_tag
def get_usertype(user, structure, label_value_tuple=False):
    label = get_user_type(user, structure)
    value = uni_ticket_settings.MANAGEMENT_URL_PREFIX[label]
    if label_value_tuple:
        return (label, value)
    return value


@register.simple_tag
def get_label_from_form(form, field_name):
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
    for m in inspect.getmembers(dynamic_fields, inspect.isclass):
        if m[0] == value:
            return getattr(m[1], "field_type")
    return value


@register.simple_tag
def get_unread_messages(ticket, by_operator=True):
    return ticket.get_messages_count(by_operator)[1]


@register.simple_tag
def user_from_pk(user_id):
    if not user_id:
        return False
    user_model = get_user_model()
    user = user_model.objects.get(pk=user_id)
    if not user:
        return False
    return user


@register.simple_tag
def user_operator_chat(user, structure):
    return user_is_in_default_office(user, structure)


@register.simple_tag
def settings_value(name, **kwargs):
    value = getattr(settings, name) \
            if hasattr(settings, name) \
            else getattr(uni_ticket_settings, name, None)
    if value and kwargs:
        return value.format(**kwargs)
    return value


@register.simple_tag
def obj_get_attr(obj, attr, **kwargs):
    return getattr(obj, attr, None)


@register.filter()
@stringfilter
def markdown(value):
    return md.markdown(value, extensions=["markdown.extensions.fenced_code"])


@register.simple_tag
def ticket_has_been_taken(ticket, user=None, structure=None, exclude_readonly=False):
    return ticket.has_been_taken(
        user=user, structure=structure, exclude_readonly=exclude_readonly
    )


@register.simple_tag
def ticket_is_open(ticket, user=None):
    return ticket.is_open(user)


@register.simple_tag
def app_is_installed(name):
    return name in settings.INSTALLED_APPS
