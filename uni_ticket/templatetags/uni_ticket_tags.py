import datetime
import inspect
import locale
import markdown as md
import os

from django import template
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.translation import gettext as _
from django.template.defaultfilters import stringfilter

from django_form_builder import dynamic_fields
from uni_ticket.models import (Ticket,
                               TicketAssignment,
                               TicketCategoryCondition,
                               TicketCategoryModule)
from uni_ticket import settings as uni_ticket_settings
from uni_ticket.utils import (download_file,
                              format_slugged_name,
                              get_user_type,
                              office_can_be_deleted,
                              user_is_in_default_office,
                              user_manage_something)

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
    return range(2019, timezone.localdate().year+1)

@register.simple_tag
def current_date():
    tz = timezone.get_current_timezone()
    now = datetime.datetime.now(tz)
    return now.strftime('%A, %d %B %Y')

@register.simple_tag
def ticket_in_category(category):
    result = 0
    office = category.organizational_office
    tickets = TicketAssignment.get_ticket_in_office_list(office_list=[office,])
    return len(tickets)

@register.simple_tag
def conditions_in_category(category):
    conditions = TicketCategoryCondition.objects.filter(category=category,
                                                        is_active=True).count()
    return conditions

@register.simple_tag
def simple_user_context_name():
    return uni_ticket_settings.CONTEXT_SIMPLE_USER

@register.simple_tag
def get_usertype(user, structure, label_value_tuple=False):
    label = get_user_type(user, structure)
    value = uni_ticket_settings.MANAGEMENT_URL_PREFIX[label]
    if label_value_tuple: return (label, value)
    return value

@register.simple_tag
def get_label_from_form(form, field_name):
    field = form.fields.get(field_name)
    if field: return field.label
    return False

@register.filter
def get_dyn_field_name(value):
    for m in inspect.getmembers(dynamic_fields, inspect.isclass):
        if m[0]==value: return getattr(m[1], 'field_type')
    return value

@register.simple_tag
def get_unread_messages(ticket, by_operator=True):
    return ticket.get_messages_count(by_operator)[1]

@register.simple_tag
def user_from_pk(user_id):
    if not user_id: return False
    user_model = get_user_model()
    user = user_model.objects.get(pk=user_id)
    if not user: return False
    return user

@register.simple_tag
def user_operator_chat(user, structure):
    return user_is_in_default_office(user, structure)

@register.simple_tag
def settings_value(name, **kwargs):
    value = getattr(settings, name, None) or getattr(uni_ticket_settings, name, None)
    if value and kwargs: return value.format(**kwargs)
    return value

@register.filter()
@stringfilter
def markdown(value):
    return md.markdown(value, extensions=['markdown.extensions.fenced_code'])

@register.simple_tag
def ticket_has_been_taken(ticket, user=None):
    return ticket.has_been_taken(user)
