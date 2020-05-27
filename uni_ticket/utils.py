import base64
import json
import logging
import magic
import operator
import os
import random
import re
import shutil
import shortuuid
import zlib

from django.apps import apps
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext as _

from django_form_builder.utils import get_POST_as_json

from io import StringIO, BytesIO

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
    # if user.is_superuser: return True
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
                                recipient=user,
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
def send_custom_mail(subject, recipient, body, params={}, force=False):
    if not recipient: return False
    if not force and not recipient.email_notify: return False

    msg_body_list = [settings.MSG_HEADER, body,
                     settings.MSG_FOOTER]
    msg_body = ''.join([i.__str__() for i in msg_body_list]).format(**params)
    result = send_mail(subject=subject,
                       message=msg_body,
                       from_email=settings.EMAIL_SENDER,
                       recipient_list=[recipient.email,],
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

def ticket_protocol(user,
                    subject,
                    configuration=None,
                    file_name='test_name',
                    response=b'',
                    attachments_folder=settings.MEDIA_ROOT,
                    attachments_dict={},
                    test=False):

    # Check only if protocol system works
    if test and not configuration:
        prot_url = settings.PROT_TEST_URL
        prot_login = settings.PROT_TEST_LOGIN
        prot_passw = settings.PROT_TEST_PASSW
        prot_aoo = settings.PROT_TEST_AOO
        prot_agd = settings.PROTOCOLLO_AGD_DEFAULT
        prot_uo = settings.PROTOCOLLO_UO_DEFAULT
        prot_id_uo = settings.PROTOCOLLO_UO_ID_DEFAULT
        prot_titolario = settings.PROTOCOLLO_TITOLARIO_DEFAULT
        prot_fascicolo_num = settings.PROTOCOLLO_FASCICOLO_DEFAULT
        prot_fascicolo_anno = settings.PROTOCOLLO_FASCICOLO_ANNO_DEFAULT
        prot_template = settings.PROTOCOL_XML
    # check my configuration in test environment
    elif test and configuration:
        prot_url = settings.PROT_TEST_URL
        prot_login = settings.PROT_TEST_LOGIN
        prot_passw = settings.PROT_TEST_PASSW
        prot_aoo = configuration.protocollo_aoo
        prot_agd = configuration.protocollo_agd
        prot_uo = configuration.protocollo_uo
        prot_id_uo = configuration.protocollo_id_uo
        prot_titolario = configuration.protocollo_cod_titolario
        prot_fascicolo_num = configuration.protocollo_fascicolo_numero
        prot_fascicolo_anno = configuration.protocollo_fascicolo_anno
        prot_template = configuration.protocollo_template
    # for production
    elif not test and configuration:
        prot_url = settings.PROT_URL
        prot_login = settings.PROT_LOGIN
        prot_passw = settings.PROT_PASSW
        prot_aoo = configuration.protocollo_aoo
        prot_agd = configuration.protocollo_agd
        prot_uo = configuration.protocollo_uo
        prot_id_uo = configuration.protocollo_id_uo
        prot_titolario = configuration.protocollo_cod_titolario
        prot_fascicolo_num = configuration.protocollo_fascicolo_numero
        prot_fascicolo_anno = configuration.protocollo_fascicolo_anno
        prot_template = configuration.protocollo_template
    # for production a custom configuration is necessary
    elif not test and not configuration:
        raise Exception(_('Missing XML configuration for production'))

    protocol_data = {
                     # 'wsdl_url' : prot_url,
                     # 'username' : prot_login,
                     # 'password' : prot_passw,
                     # 'template_xml_flusso': prot_template,

                      # Variabili
                     'oggetto':'{}'.format(subject),
                     # 'matricola_dipendente': user.matricola_dipendente,
                     'id_persona': user.taxpayer_id,
                     'nome_persona': user.first_name,
                     'cognome_persona': user.last_name,
                     'denominazione_persona': ' '.join((user.first_name,
                                                        user.last_name,)),

                     # attributi creazione protocollo
                     'aoo': prot_aoo,
                     'agd': prot_agd,
                     'uo': prot_uo,
                     'uo_id': prot_id_uo,
                     'id_titolario': prot_titolario,
                     'fascicolo_numero': prot_fascicolo_num,
                     'fascicolo_anno': prot_fascicolo_anno
                    }

    protclass = __import__(settings.CLASSE_PROTOCOLLO, globals(), locals(), ['*'])

    # wsclient = protclass.Protocollo(**protocol_data)
    wsclient = protclass.Protocollo(wsdl_url=prot_url,
                                    username=prot_login,
                                    password=prot_passw,
                                    template_xml_flusso=prot_template,
                                    strictly_required=True,
                                    **protocol_data)

    logger.info('Protocollazione richiesta {}'.format(subject))
    docPrinc = BytesIO()
    docPrinc.write(response)
    docPrinc.seek(0)

    wsclient.aggiungi_docPrinc(docPrinc,
                               nome_doc="{}.pdf".format(file_name),
                               tipo_doc='uniTicket request')

    # attachments
    if attachments_dict:
        for k,v in attachments_dict.items():
            file_path = '{}/{}/{}'.format(settings.MEDIA_ROOT,
                                          attachments_folder,
                                          v)
            mime = magic.Magic(mime=True)
            content_type = mime.from_file(file_path)
            f = open(file_path, 'rb')
            attachment_response = HttpResponse(f.read(), content_type=content_type)
            attachment_response['Content-Disposition'] = 'inline; filename=' + v
            f.close()
            allegato = BytesIO()
            allegato.write(attachment_response.content)
            allegato.seek(0)
            wsclient.aggiungi_allegato(nome=v,
                                       descrizione=subject,
                                       fopen=allegato)

    # print(wsclient.is_valid())
    logger.debug(wsclient.render_dataXML())
    # print(wsclient.render_dataXML())
    prot_resp = wsclient.protocolla()

    # logger.info('Avvenuta Protocollazione Richiesta {} numero: {}'.format(form.cleaned_data['subject'],
                                                                          # domanda_bando.numero_protocollo))
    # raise exception if wsclient hasn't a protocol number
    assert wsclient.numero
    return wsclient.numero
