import base64
import json
import magic
import os
import shutil
import shortuuid

from django.apps import apps
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext as _

from django_form_builder.utils import get_POST_as_json
from organizational_area.models import (OrganizationalStructure,
                                        OrganizationalStructureOffice,
                                        OrganizationalStructureOfficeEmployee)

from . settings import *


def custom_message(request, message='', structure_slug=''):
    """
    """
    return render(request, 'custom_message.html',
                  {'avviso': message,
                   'structure_slug': structure_slug})

def user_manage_something(user):
    """
    Tells us if the user is a manager or operator in some structure/office
    """
    if not user: return False
    osoe = OrganizationalStructureOfficeEmployee
    employee_offices = osoe.objects.filter(employee=user,
                                           office__is_active=True)
    if not employee_offices: return False
    structures = []
    for eo in employee_offices:
        structure = eo.office.organizational_structure
        if structure.is_active and structure not in structures:
            structures.append(structure)
    return structures

def user_is_manager(user, structure):
    """
    Returns True if user is a manager for the structure
    """
    if not user.is_staff: return False
    if not structure: return False
    return user_is_in_default_office(user, structure)

def user_is_in_default_office(user, structure):
    """
    Returns True is user is assigned to structure default office
    """
    if not user or not structure: return False
    osoe = OrganizationalStructureOfficeEmployee
    help_desk_assigned = osoe.objects.filter(employee=user,
                                             office__organizational_structure=structure,
                                             office__is_default=True).first()
    if help_desk_assigned: return True
    return False

def user_is_operator(user, structure):
    """
    Returns OrganizationalStructureOfficeEmployee queryset
    if user is a operator of an office for the structure
    """
    if not user: return False
    if not structure: return False
    osoe = OrganizationalStructureOfficeEmployee
    oe = osoe.objects.filter(employee=user,
                             office__organizational_structure=structure,
                             office__is_active=True)
    if oe: return oe

def user_manage_office(user, office):
    """
    Returns True if user is a operator of an office for the structure
    """
    if not user: return False
    if not office: return False
    if not office.is_active: return False
    # If user is an operator of structure's default office,
    # than he can manage tickets of other offices too
    if user_is_in_default_office(user, office.organizational_structure):
        return True
    osoe = OrganizationalStructureOfficeEmployee
    oe = osoe.objects.filter(employee=user, office=office).first()
    if oe: return True
    return False

def get_user_type(user, structure=None):
    """
    Returns user-type in ticket system hierarchy
    """
    if not structure: return 'user'
    if user_is_manager(user, structure): return 'manager'
    if user_is_operator(user, structure): return 'operator'
    return 'user'

def get_folder_allegato(ticket):
    """
    Returns ticket attachments folder path
    """
    folder = '{}/{}/{}/{}'.format(settings.HOSTNAME,
                                  ticket.get_year(),
                                  TICKET_ATTACHMENT_FOLDER,
                                  ticket.code)
    return folder

def get_path_allegato(ticket):
    """
    Builds ticket attachments path
    """
    folder = get_folder_allegato(ticket=ticket)
    path = '{}/{}'.format(settings.MEDIA_ROOT, folder)
    return path

def get_path_allegato_task(task):
    """
    Builds task attachments path
    """
    ticket_folder = get_path_allegato(ticket=task.ticket)
    path = '{}/{}/{}'.format(ticket_folder,
                             TICKET_TASK_ATTACHMENT_SUBFOLDER,
                             task.code)
    return path

def get_path_ticket_reply(ticket_reply):
    """
    Builds ticket messages attachments path
    """
    ticket_folder = get_path_allegato(ticket=ticket_reply.ticket)
    path = '{}/{}'.format(ticket_folder,
                          TICKET_MESSAGES_ATTACHMENT_SUBFOLDER)
    return path

def delete_file(file_name, path=settings.MEDIA_ROOT):
    """
    Deletes a file from disk
    """
    file_path = '{}/{}'.format(path,file_name)
    try:
        os.remove(file_path)
        return path
    except:
        return False

def delete_directory(ticket_id):
    """
    Deletes a ticket attachments directory from disk
    """
    path = '{}/{}/{}'.format(settings.MEDIA_ROOT,
                             TICKET_ATTACHMENT_FOLDER,
                             ticket_id)
    try:
        shutil.rmtree(path)
        return path
    except:
        return False

def save_file(f, path, nome_file):
    """
    Saves a file on disk
    """
    file_path = '{}/{}'.format(path,nome_file)

    if not os.path.exists(os.path.dirname(file_path)):
        os.makedirs(os.path.dirname(file_path))
    with open(file_path,'wb') as destination:
        for chunk in f.chunks():
            destination.write(chunk)

def download_file(path, nome_file):
    """
    Downloads a file
    """
    mime = magic.Magic(mime=True)
    file_path = '{}/{}'.format(path,nome_file)
    content_type = mime.from_file(file_path)

    if os.path.exists(file_path):
        with open(file_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type=content_type)
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(file_path)
            return response
    return None

def format_slugged_name(field_name, capitalize=True):
    """
    Makes a string slugged
    """
    f = field_name.replace('_',' ')
    if capitalize: return f.capitalize()
    return f

def visible_tickets_to_user(user, structure, office_employee):
    """
    Returns a list of tickets that are visible to user
    """
    model = apps.get_model('uni_ticket', 'TicketAssignment')
    # default_office = office_employee.filter(office__is_default=True).first()
    # if default_office:
    if user_is_in_default_office(user, structure):
        tickets = model.get_ticket_per_structure(structure)
        return tickets
    offices = []
    for oe in office_employee:
        if oe.office not in offices:
            offices.append(oe.office)
    tickets = model.get_ticket_in_office_list(offices)
    return tickets

def office_can_be_deleted(office):
    """
    Returns True if office can be deleted
    """
    if not office: return False
    if office.is_default: return False
    model = apps.get_model('uni_ticket', 'TicketAssignment')
    ticket_assegnati = model.objects.filter(office=office)
    if ticket_assegnati: return False
    return True

def uuid_code():
    """
    Returns a short uuid code
    """
    return shortuuid.uuid()

# Not used!
# def ticket_summary_dict():
    # """
    # returns a dictionary with {office_obj: [list of assigned tickets {subject, url}],}
    # for every office
    # """
    # model = apps.get_model('uni_ticket', 'Ticket')
    # tickets = model.objects.exclude(is_closed=True)
    # assign_model = apps.get_model('uni_ticket', 'TicketAssignment')

    # summary_dict = dict()
    # offices = OrganizationalStructureOffice.objects.filter(is_active=True)
    # for office in offices:
        # assignments = assign_model.objects.filter(office=office,
                                                  # follow=True,
                                                  # ticket__is_closed=False)
        # if not summary_dict.get(office):
            # summary_dict[office] = []

        # for ticket in assignments:
            # summary_dict[office].append({'subject': ticket.ticket.subject,
                                         # 'url': ticket.ticket.get_url(structure=office.organizational_structure)})
    # return summary_dict

def ticket_user_summary_dict(user):
    assign_model = apps.get_model('uni_ticket', 'TicketAssignment')
    structures = OrganizationalStructure.objects.filter(is_active=True)
    d = dict()
    oso = OrganizationalStructureOffice
    osoe = OrganizationalStructureOfficeEmployee
    office_employee = osoe.objects.filter(employee=user)
    for structure in structures:
        d[structure] = {}
        user_type = get_user_type(user, structure)
        offices = oso.objects.filter(organizational_structure=structure,
                                     is_active=True)
        for office in offices:
            if user_type == 'operator' and not office in office_employee:
                continue
            assignments = assign_model.objects.filter(office=office,
                                                      follow=True,
                                                      ticket__is_closed=False)
            if not d.get(office):
                d[structure][office] = []

            for ticket in assignments:
                d[structure][office].append({'subject': ticket.ticket.subject,
                                             'url': ticket.ticket.get_url(structure=structure)})
    return d

def send_summary_email(users=[]):
    failed = []
    success = []
    for user in users:
        if not user.email:
            failed.append(user)
            continue
        msg = []
        ticket_sum = 0
        tick_sum = ticket_user_summary_dict(user)
        for structure in tick_sum:
            if not tick_sum[structure]: continue
            msg.append('{}:\n'.format(structure))
            for office in tick_sum[structure]:
                if not tick_sum[structure][office]: continue
                msg.append('{} tickets in {}:\n'.format(len(tick_sum[structure][office]),
                                                            office.name))
                for ticket in tick_sum[structure][office]:
                    ticket_sum += 1
                    msg.append(' - {} (http://{}{})\n'.format(ticket['subject'],
                                                              settings.HOSTNAME,
                                                              ticket['url']))
            msg.append('\n')

        d = {'open_ticket_number': ticket_sum,
             'tickets_per_office': ''.join(msg),
             'hostname': settings.HOSTNAME,
             'user': user}
        m_subject = _('{} - ticket summary'.format(settings.HOSTNAME))

        sent = send_custom_mail(subject=m_subject,
                                recipient=user,
                                body=SUMMARY_EMPLOYEE_EMAIL,
                                params=d)
        if not sent:
            failed.append(user)
        else:
            success.append(user)

    return {'success': success,
            'failed': failed}

def user_offices_list(office_employee_queryset):
    if not office_employee_queryset: return []
    offices = []
    for oe in office_employee_queryset:
        if oe.office not in offices:
            offices.append(oe.office)
    return offices

# Custom email sender
def send_custom_mail(subject, recipient, body, params={}):
    if not recipient: return False
    if not recipient.email_notify: return False

    msg_body_list = [MSG_HEADER, body, MSG_FOOTER]
    msg_body = ''.join(msg_body_list).format(**params)
    result = send_mail(subject=subject,
                       message=msg_body,
                       from_email=settings.EMAIL_SENDER,
                       recipient_list=[recipient.email,],
                       fail_silently=True,
                       auth_user=None,
                       auth_password=None,
                       connection=None,
                       html_message=None)
    return result

# START Roles 'get' methods
def user_is_employee(user):
    if not user: return False
    if getattr(settings, 'EMPLOYEE_ATTRIBUTE_NAME', False):
        attr = getattr(user, settings.EMPLOYEE_ATTRIBUTE_NAME)
        if callable(attr): return attr()
        else: return attr
    # If operator in the same Structure
    # is_operator = user_is_operator(request.user, struttura)
    # If manage something. For alla structures
    return user_manage_something(user)

def user_is_in_organization(user):
    """
    """
    if not user: return False
    if getattr(settings, 'USER_ATTRIBUTE_NAME', False):
        attr = getattr(user, settings.USER_ATTRIBUTE_NAME)
        if callable(attr): return attr()
        else: return attr
    return False
# END Roles 'get' methods


