import base64
import datetime
import csv
import io
import json
import logging
import magic
import operator
import os
import random
import re
import shutil
import shortuuid
import zipfile
import zlib

from django.apps import apps
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone
from django.utils.html import strip_tags
from django.utils.translation import gettext as _

from django_form_builder.utils import get_POST_as_json, format_field_name

from organizational_area.models import (OrganizationalStructure,
                                        OrganizationalStructureOffice,
                                        OrganizationalStructureOfficeEmployee,
                                        UserManageOrganizationalStructure)


logger = logging.getLogger(__name__)


def compress_text_to_b64(text):
    """Returns a compressed and b64 encoded string
    """
    if isinstance(text, str):
        text = text.encode()
    return base64.b64encode(zlib.compress(text))


def decompress_text(b64text):
    """Returns a decompressed string
    """
    if isinstance(b64text, str):
        b64text = b64text.encode()
    return zlib.decompress(base64.b64decode(b64text))


def custom_message(request, message='', structure_slug='', status=None):
    """
    """
    return render(request, 'custom_message.html',
                  {'avviso': message,
                   'structure_slug': structure_slug},
                  status=status)

def user_manage_something(user):
    """
    Tells us if the user is a manager or operator in some structure/office
    """
    if not user: return False
    if settings.SUPER_USER_VIEW_ALL and user.is_superuser:
        structures = OrganizationalStructure.objects.filter(is_active=True)
    else:
        osoe = OrganizationalStructureOfficeEmployee
        employee_offices = osoe.objects.filter(employee=user,
                                               office__is_active=True)
        if not employee_offices: return False
        structures = []
        for eo in employee_offices:
            structure = eo.office.organizational_structure
            if structure.is_active and structure not in structures:
                structures.append(structure)
    return sorted(structures, key=operator.attrgetter("name"))

def user_is_manager(user, structure):
    """
    Returns True if user is a manager for the structure
    """
    if settings.SUPER_USER_VIEW_ALL and user.is_superuser: return True
    umos = UserManageOrganizationalStructure
    user_structure_manager = umos.objects.filter(user=user,
                                                 organizational_structure=structure).first()
    if not user_structure_manager: return False
    if not structure: return False
    return user_is_in_default_office(user, structure)

def user_is_in_default_office(user, structure):
    """
    Returns True is user is assigned to structure default office
    """
    if not user or not structure: return False
    if settings.SUPER_USER_VIEW_ALL and user.is_superuser: return True
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

def user_manage_office(user, office, strictly_assigned=False):
    """
    Returns True if user is a operator of an office for the structure
    """
    if not user: return False
    if not office: return False
    if not office.is_active: return False
    # If user is an operator of structure's default office,
    # than he can manage tickets of other offices too
    if not strictly_assigned and user_is_in_default_office(user, office.organizational_structure):
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

def get_path(folder):
    """
    Builds a MEDIA_ROOT path
    """
    return '{}/{}'.format(settings.MEDIA_ROOT, folder)
    return path

def delete_file(file_name, path=settings.MEDIA_ROOT):
    """
    Deletes a file from disk
    """
    file_path = '{}/{}'.format(path, file_name)
    try:
        os.remove(file_path)
        return path
    except:
        return False

def delete_directory(path):
    """
    Deletes a ticket attachments directory from disk
    """
    path = '{}/{}'.format(settings.MEDIA_ROOT, path)
    try:
        shutil.rmtree(path)
        return path
    except:
        logger.error('Error removing folder{}'.format(path))
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
                                                      readonly=False,
                                                      ticket__is_closed=False)
            if assignments:
                d[structure][office] = []
                for assignment in assignments:
                    d[structure][office].append({'subject': assignment.ticket.subject,
                                                 'code': assignment.ticket.code,
                                                 'url': assignment.ticket.get_url(structure=structure)})
        if not d[structure]:
            del d[structure]
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
        assignments_dict = ticket_user_summary_dict(user)
        ticket_code_list = []
        for structure in assignments_dict:
            if not assignments_dict[structure]: continue
            msg.append('{}:\n'.format(structure))
            for office in assignments_dict[structure]:
                msg.append('{} tickets in {}:\n'.format(len(assignments_dict[structure][office]),
                                                            office.name))
                for ticket in assignments_dict[structure][office]:
                    if ticket['code'] not in ticket_code_list:
                        ticket_sum += 1
                        ticket_code_list.append(ticket['code'])
                    msg.append(' - {} (http://{}{})\n'.format(ticket['subject'],
                                                              settings.HOSTNAME,
                                                              ticket['url']))
            msg.append('\n')

        d = {'opened_ticket_number': ticket_sum,
             'tickets_per_office': ''.join(msg),
             'hostname': settings.HOSTNAME,
             'user': user}
        m_subject = _('{} - ticket summary'.format(settings.HOSTNAME))

        sent = send_custom_mail(subject=m_subject,
                                recipients=[user],
                                body=settings.SUMMARY_EMPLOYEE_EMAIL,
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
def send_custom_mail(subject, recipients, body, params={}, force=False):
    if not recipients: return False
    recipients_list = []
    for recipient in recipients:
        if not recipient.email: continue
        if not force and not recipient.email_notify: continue
        recipients_list.append(recipient.email)

    if recipients_list:
        msg_body_list = [settings.MSG_HEADER, body,
                         settings.MSG_FOOTER]
        msg_body = ''.join([i.__str__() for i in msg_body_list]).format(**params)
        result = send_mail(subject=subject,
                           message=msg_body,
                           from_email=settings.EMAIL_SENDER,
                           recipient_list=recipients_list,
                           fail_silently=True)
        return result

# START Roles 'get' methods
def user_is_employee(user):
    if not user: return False
    if getattr(settings, 'EMPLOYEE_ATTRIBUTE_NAME', False):
        attr = getattr(user, settings.EMPLOYEE_ATTRIBUTE_NAME)
        if callable(attr): return attr()
        else: return attr
    return False
    # If operator in the same Structure
    # is_operator = user_is_operator(request.user, struttura)
    # If manage something. For alla structures
    # return user_manage_something(user)

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

def get_text_with_hrefs(text):
    """Transforms a text with url in text with <a href=></a> tags
       text = ("Allora considerando quanto scritto quì "
               "https://ingoalla.it/sdfsd/.well-known/ini.php?sdf=3244&df23=FDS3_ "
               "dovresti piuttosto - se vuoi - andare qui "
               "http://rt4t.ty/546-546-56546 oppure "
               "https://mdq.auth.unical.it:8000/entities/https%3A%2F%2Fidp.unical.it%2Fidp%2Fshibboleth")
    get_text_with_hrefs(text)
    """
    new_text = ''.join([ch for ch in text])
    href_tmpl = '<a target="{}" href="{}">{}</a>'
    regexp = re.compile('https?://[\.A-Za-z0-9\-\_\:\/\?\&\=\+\%]*', re.I)
    for ele in re.findall(regexp, text):
        target = str(random.random())[2:]
        a_value = href_tmpl.format(target, ele, ele)
        new_text = new_text.replace(ele, a_value)
    return new_text

def get_datetime_delta(days):
    delta_date = timezone.now() - datetime.timedelta(days=days)
    return delta_date.replace(hour=0, minute=0, second=0)

def disable_not_in_progress_categories(categories):
    for category in categories:
        if not category.is_in_progress():
            category.is_active = False
            category.save(update_fields=['is_active'])

def export_category_zip(category):
    formset_re = "^{}-(?P<index>[0-9]+)-(?P<name>[a-zA-Z0-9_\-]+)$"

    output = io.BytesIO()
    f = zipfile.ZipFile(output, 'w', zipfile.ZIP_DEFLATED)

    delimiter='$'
    quotechar='"'
    dialect='excel'

    try:
        input_modules = apps.get_model('uni_ticket', 'TicketCategoryModule').objects.filter(ticket_category=category)
        for module in input_modules:
            file_name = "{}_MOD_{}_{}.csv".format(category.name.replace('/','_'),
                                                  module.created.strftime('%Y-%m-%d_%H-%M-%S'),
                                                  module.name.replace('/','_'))
            head = ['created',
                    'user',
                    'status',
                    'subject',
                    'description']
            custom_head = []
            fields = apps.get_model('uni_ticket', 'TicketCategoryInputList').objects.filter(category_module=module)
            for field in fields:
                custom_head.append(field.name)
                head.append(field.name)
            csv_file = HttpResponse(content_type='text/csv')
            csv_file['Content-Disposition'] = 'attachment; filename="{}"'.format(file_name)
            writer = csv.writer(csv_file,
                                dialect=dialect,
                                delimiter = delimiter,
                                quotechar = quotechar)

            writer.writerow(head)
            richieste = apps.get_model('uni_ticket', 'Ticket').objects.filter(input_module=module)
            if not richieste: continue

            for richiesta in richieste:
                content = richiesta.get_modulo_compilato()

                status = strip_tags(richiesta.get_status())
                row = [richiesta.created,
                       richiesta.created_by,
                       status,
                       richiesta.subject,
                       richiesta.description]
                for column in custom_head:
                    name = format_field_name(column)
                    match_list = ''
                    for_index = 0
                    formset_index = 0
                    for k,v in content.items():
                        found = re.search(formset_re.format(name), k)
                        if found:
                            if for_index != 0:
                                match_list += '\n'
                            if int(found.group('index')) > formset_index:
                                match_list += '\n'
                                formset_index += 1
                            for_index += 1
                            match_list += '{}: {}'.format(found.group('name'), v)
                    if match_list:
                        row.append(match_list)
                    else:
                        row.append(content.get(name, ''))
                writer.writerow(row)
            f.writestr(file_name,
                       csv_file.content)
    except Exception as e:
        logger.error('Error export category {}: {}'.format(category, e))

    f.close()
    response = HttpResponse(output.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = 'attachment; filename="{}.zip"'.format(category.name.replace('/','_'))
    return response
