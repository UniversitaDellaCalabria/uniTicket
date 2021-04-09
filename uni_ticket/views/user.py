import os
import json
import logging
import re
import shutil

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.models import LogEntry, ADDITION, CHANGE
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.db.models import Q
from django.forms import formset_factory
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.html import strip_tags
from django.utils.translation import gettext as _

from django_form_builder.utils import (get_as_dict,
                                       get_labeled_errors,
                                       get_POST_as_json,
                                       set_as_dict)
from organizational_area.models import (OrganizationalStructure,
                                        OrganizationalStructureOffice,
                                        OrganizationalStructureOfficeEmployee,)
# from PyPDF2 import PdfFileMerger

from uni_ticket.decorators import *
from uni_ticket.forms import *
from uni_ticket.jwts import *
from uni_ticket.models import *
from uni_ticket.pdf_utils import response_as_pdf
from uni_ticket.protocol_utils import ticket_protocol
from uni_ticket.utils import *


logger = logging.getLogger(__name__)


# assign category default tasks to new ticket created by user
def _assign_default_tasks_to_new_ticket(ticket, category, log_user):
    tasks = category.get_tasks(is_active=True)
    for task in tasks:
        ticket_task = Task()
        ticket_task.ticket = ticket
        ticket_task.subject = task.subject
        ticket_task.description = task.description
        ticket_task.priority = task.priority
        ticket_task.is_public = task.is_public
        ticket_task.created_by = task.created_by
        ticket_task.code = uuid_code()
        ticket_task.attachment = task.attachment
        ticket_task.save()

        # copy category task attachments in ticket task folder
        if task.attachment:
            source = '{}/{}'.format(settings.MEDIA_ROOT,
                                    task.get_folder())
            destination = '{}/{}'.format(settings.MEDIA_ROOT,
                                         ticket_task.get_folder())
            try:
                if os.path.exists(source):
                    shutil.copytree(source, destination)
            except:
                logger.error('[{}] {} try to copy not existent folder {}'
                             ''.format(timezone.localtime(),
                                       log_user,
                                       source))

# close ticket as soon as opened if it's a notification ticket
def _close_notification_ticket(ticket, user): # operator, ticket_assignment):
    # close ticket
    ticket.is_notification = True
    ticket.is_closed = True
    ticket.closed_date = timezone.localtime()
    # ticket.closed_by = user
    # default closing status: success
    ticket.closing_status = 1
    ticket.save(update_fields=['is_notification',
                               'is_closed',
                               'closed_date',
                               'closing_status'])
                               # 'closed_by'])

    # assign to an operator
    # ticket_assignment.taken_date = timezone.localtime()
    # ticket_assignment.taken_by = operator
    # ticket_assignment.save(update_fields=['taken_date', 'taken_by'])

# save attachments of new ticket
def _save_new_ticket_attachments(ticket,
                                 json_stored,
                                 form,
                                 request_files):
    if request_files:
        if not json_stored.get(settings.ATTACHMENTS_DICT_PREFIX):
            json_stored[settings.ATTACHMENTS_DICT_PREFIX] = {}
        path_allegati = get_path(ticket.get_folder())
        attach_key = ''
        attach_value = ''

        for key, value in request_files.items():
            formset_regex = re.match(settings.FORMSET_FULL_REGEX, key)
            if formset_regex:
                formset_field = form.fields[formset_regex['field_name']]
                if formset_field.is_formset:
                    sub_field_name = formset_regex['name']
                    index = formset_regex['index']
                    formset_data = formset_field.widget.formset.forms[int(index)].cleaned_data
                    attach_key = formset_data[sub_field_name]
                    attach_value = attach_key._name
            else:
                attach_key = form.cleaned_data[key]
                attach_value = attach_key._name

            save_file(attach_key,
                      path_allegati,
                      attach_value)
            json_stored[settings.ATTACHMENTS_DICT_PREFIX][key] = attach_value

            # log action
            logger.info('[{}] attachment {} saved in {}'.format(timezone.localtime(),
                                                                attach_key,
                                                                path_allegati))

        set_as_dict(ticket, json_stored)

# send email to operators when new ticket is opened
def _send_new_ticket_mail_to_operators(request,
                                       ticket,
                                       category,
                                       message_template,
                                       mail_params):
    office = category.organizational_office
    structure = category.organizational_structure
    # mail_params = {'hostname': settings.HOSTNAME,
                   # 'ticket_url': request.build_absolute_uri(reverse('uni_ticket:manage_ticket_url_detail',
                                                                     # kwargs={'ticket_id': ticket.code,
                                                                             # 'structure_slug': structure.slug})),
                   # 'ticket_subject': ticket.subject,
                   # 'ticket_description': ticket.description,
                   # 'ticket_user': ticket.created_by,
                   # 'destination_office': office,
                  # }

    m_subject = _('{} - {}'.format(settings.HOSTNAME, category))
    operators = OrganizationalStructureOfficeEmployee.objects.filter(office=office,
                                                                     employee__is_active=True)
    # if no operators in office, get default office operators
    if not operators:
        operators = OrganizationalStructureOfficeEmployee.objects.filter(office__organizational_structure=structure,
                                                                         office__is_default=True,
                                                                         employee__is_active=True)
    recipients = []
    for op in operators:
        recipients.append(op.employee.email)

    mail_params['user'] = settings.OPERATOR_PREFIX
    msg_body_list = [settings.MSG_HEADER,
                     message_template,
                     settings.MSG_FOOTER]
    msg_body = ''.join([i.__str__() for i in msg_body_list]).format(**mail_params)
    result = send_mail(subject=m_subject,
                       message=msg_body,
                       from_email=settings.EMAIL_SENDER,
                       recipient_list=recipients,
                       fail_silently=True)
    logger.info('[{}] sent mail (result: {}) '
                'to operators for ticket {}'
                ''.format(timezone.localtime(),
                          result,
                          ticket))

@login_required
def ticket_new_preload(request, structure_slug=None):
    """
    Choose the OrganizationalStructure and the category of the ticket

    :type structure_slug: String

    :param structure_slug: slug of structure

    :return: render
    """
    if Ticket.number_limit_reached_by_user(request.user):
        messages.add_message(request, messages.ERROR,
                             _("Hai raggiunto il limite massimo giornaliero"
                               " di richieste: <b>{}</b>"
                               "").format(settings.MAX_DAILY_TICKET_PER_USER))
        return redirect(reverse('uni_ticket:user_dashboard'))

    strutture = OrganizationalStructure.objects.filter(is_active=True)
    active_alerts = []
    categorie = None
    template = "user/new_ticket_preload.html"
    title = _("Effettua una nuova richiesta")
    sub_title = _("Seleziona la struttura")
    structure = None
    if structure_slug:
        try:
            structure = get_object_or_404(OrganizationalStructure,
                                          pk=structure_slug,
                                          is_active=True)
        except:
            structure = get_object_or_404(OrganizationalStructure,
                                          slug=structure_slug,
                                          is_active=True)

        alerts = OrganizationalStructureAlert.objects.filter(organizational_structure=structure,
                                                             is_active=True)
        disabled_expired_items(alerts)
        active_alerts = [i for i in alerts if i.is_published()]

        categorie = TicketCategory.objects.filter(organizational_structure=structure,
                                                  is_active=True)

        # disabled_expired_items(categorie)
        to_be_excluded = []
        for category in categorie:
            if not category.is_published():
                to_be_excluded.append(category)
        for tbe in to_be_excluded:
            categorie = categorie.exclude(pk=tbe.pk)

        # User roles
        is_employee = user_is_employee(request.user)
        is_user = user_is_in_organization(request.user)

        if is_employee and is_user:
            categorie = categorie.filter(Q(allow_employee=True) |
                                         Q(allow_user=True) |
                                         Q(allow_guest=True))
        elif is_employee:
            categorie = categorie.filter(Q(allow_employee=True) |
                                         Q(allow_guest=True))
        elif is_user:
            categorie = categorie.filter(Q(allow_user=True) |
                                         Q(allow_guest=True))
        else:
            categorie = categorie.filter(allow_guest=True)

        sub_title = _("Seleziona la Categoria")
    d = {'alerts': active_alerts,
         'categorie': categorie,
         'chosen_structure': structure,
         'strutture': strutture,
         'sub_title': sub_title,
         'title': title,}
    return render(request, template, d)

# @login_required
def ticket_add_new(request, structure_slug, category_slug):
    """
    Create the ticket

    :type structure_slug: String
    :type category_slug: String

    :param structure_slug: slug of structure
    :param category_slug: slug of category

    :return: render
    """
    # get structure by pk or by slug
    try:
        struttura = get_object_or_404(OrganizationalStructure,
                                      pk=structure_slug,
                                      is_active=True)
    except:
        struttura = get_object_or_404(OrganizationalStructure,
                                      slug=structure_slug,
                                      is_active=True)
    # get category by pk or by slug
    try:
        category = get_object_or_404(TicketCategory,
                                     pk=category_slug,
                                     organizational_structure=struttura)
    except:
        category = get_object_or_404(TicketCategory,
                                     slug=category_slug,
                                     organizational_structure=struttura)

    # if category is not active, return an error message
    if not category.is_published():
        unavailable_msg = category.not_available_message or settings.UNAVAILABLE_TICKET_CATEGORY
        return custom_message(request, unavailable_msg, status=404)

    # if anonymous user and category only for logged users
    if not category.allow_anonymous and not request.user.is_authenticated:
        redirect_url = '{}?next={}'.format(settings.LOGIN_URL,
                                           request.get_full_path())
        return redirect(redirect_url)

    # is user is authenticated
    if request.user.is_authenticated:
        # check ticket number limit
        if Ticket.number_limit_reached_by_user(request.user):
            messages.add_message(request, messages.ERROR,
                                 _("Hai raggiunto il limite massimo giornaliero"
                                   " di richieste: <b>{}</b>"
                                   "".format(settings.MAX_DAILY_TICKET_PER_USER)))
            return redirect('uni_ticket:user_dashboard')
        # check if user is allowed to access this category
        if not category.allowed_to_user(request.user):
            return custom_message(request, _("Permesso negato a questa tipologia di utente."))

    title = category
    template = 'user/ticket_add_new.html'
    sub_title = category.description if category.description else _("Compila i campi richiesti")

    # user that compiled ticket
    compiled_by_user = None
    compiled_date = None

    # if there is an encrypted token with ticket params in URL
    if request.GET.get('import'):
        encoded_data = request.GET['import']
        try:
            # decrypt and get imported form content
            imported_data = json.loads(decrypt_from_jwe(encoded_data))
        except Exception as e:
            return custom_message(request,
                                  _("Dati da importare non consistenti."))
        # get input_module id from imported data
        module_id = imported_data.get(settings.TICKET_INPUT_MODULE_NAME)
        if not module_id:
            return custom_message(request,
                                  _("Dati da importare non consistenti. "
                                    "Modulo di input mancante"))
        modulo = get_object_or_404(TicketCategoryModule,
                                   ticket_category=category,
                                   pk=module_id)
        # get user that compiled module (if exists)
        compiled_by_user_id = imported_data.get(settings.TICKET_COMPILED_BY_USER_NAME)
        if compiled_by_user_id:
            compiled_by_user = get_user_model().objects.filter(pk=compiled_by_user_id).first()
            compiled_date = parse_datetime(imported_data.get(settings.TICKET_COMPILED_CREATION_DATE)) \
                            if imported_data.get(settings.TICKET_COMPILED_CREATION_DATE) \
                            else timezone.localtime()
        # get compiled form
        form = modulo.get_form(data=imported_data,
                               show_conditions=True,
                               current_user=request.user)
    else:
        modulo = get_object_or_404(TicketCategoryModule,
                                   ticket_category=category,
                                   is_active=True)
        form = modulo.get_form(show_conditions=True,
                               current_user=request.user)

    clausole_categoria = category.get_conditions()
    d={'categoria': category,
       'category_conditions': clausole_categoria,
       'compiled_by': compiled_by_user,
       'form': form,
       'struttura': struttura,
       'sub_title': '{} - {}'.format(struttura, sub_title),
       'title': title}

    # after form submit
    if request.POST:
        form = modulo.get_form(data=request.POST,
                               files=request.FILES,
                               show_conditions=True,
                               current_user=request.user)
        d['form'] = form

        if form.is_valid():
            # add static static fields to fields to pop
            # these fields are useful only in frontend
            fields_to_pop = [settings.TICKET_CONDITIONS_FIELD_ID,
                             settings.TICKET_CAPTCHA_ID,
                             settings.TICKET_CAPTCHA_HIDDEN_ID]
            #
            # if user generates an encrypted token in URL
            # no ticket is saved. compiled form is serialized
            #
            if request.POST.get(settings.TICKET_GENERATE_URL_BUTTON_NAME):

                # log action
                logger.info('[{}] user {} generated a new ticket URL "{}" '
                            'for submission'.format(timezone.localtime(),
                                                    request.user,
                                                    category))

                # add the "generate url" button to fields to pop
                fields_to_pop.append(settings.TICKET_GENERATE_URL_BUTTON_NAME)

                # get form data in json
                json_data = get_POST_as_json(request=request,
                                             fields_to_pop=fields_to_pop)
                form_data = json.loads(json_data)

                # insert input module pk to json data
                form_data.update({settings.TICKET_INPUT_MODULE_NAME: modulo.pk})

                if request.POST.get(settings.TICKET_COMPILED_BY_USER_NAME):
                    form_data.update({settings.TICKET_COMPILED_BY_USER_NAME: request.user.pk})
                    form_data.update({settings.TICKET_COMPILED_CREATION_DATE: timezone.localtime().isoformat()})

                # build encrypted url param with form data
                encrypted_data = encrypt_to_jwe(json.dumps(form_data).encode())
                base_url = request.build_absolute_uri(reverse('uni_ticket:add_new_ticket',
                                                              kwargs={'structure_slug': struttura.slug,
                                                                      'category_slug': category.slug}))
                # build url to display in message
                url = base_url + '?import=' + encrypted_data
                messages.add_message(request, messages.SUCCESS,
                                     _("<b>Di seguito l'URL della richiesta precompilata</b>"
                                       "<input type='text' value='{url}' id='encrypted_ticket_url' />"
                                       "<button class='btn btn-sm btn-primary px-4 mt-3' onclick='copyToClipboard()'>"
                                       "Copia negli appunti"
                                       "</button>"
                                       "<p class='text-success mt-3 mb-0' id='clipboard_message'></p>"
                                       "").format(url=url))
                d['url_to_import'] = True
            #
            # if user creates the ticket
            #
            elif request.POST.get(settings.TICKET_CREATE_BUTTON_NAME):

                # if user is not allowed (category allowed users list)
                if category.allowed_users.all() and request.user not in category.allowed_users.all():
                    return custom_message(request,
                                          _("Solo gli utenti abilitati "
                                            "possono generare richieste "
                                            "di questo tipo"),
                                          status=404)

                # extends fields_to_pop list
                fields_to_pop.extend([settings.TICKET_SUBJECT_ID,
                                      settings.TICKET_DESCRIPTION_ID,
                                      settings.TICKET_CREATE_BUTTON_NAME,
                                      settings.TICKET_COMPILED_BY_USER_NAME,
                                      settings.TICKET_COMPILED_CREATION_DATE])

                # get form data in json
                json_data = get_POST_as_json(request=request,
                                             fields_to_pop=fields_to_pop)

                # make a UUID based on the host ID and current time
                code = uuid_code()

                # get ticket subject and description
                subject = form.cleaned_data[settings.TICKET_SUBJECT_ID]
                description = form.cleaned_data[settings.TICKET_DESCRIPTION_ID]

                # destination office
                office = category.organizational_office

                # take a random operator (or manager)
                # only if category is_notification or user is anonymous
                random_office_operator = None
                if category.is_notification or not request.user.is_authenticated:
                    # get random operator from the office
                    random_office_operator = OrganizationalStructureOfficeEmployee.get_default_operator_or_manager(office)

                # set users for current operations and for log
                # if current_user isn't authenticated, for logging we use 'anonymous'
                current_user = request.user if request.user.is_authenticated else random_office_operator
                log_user = request.user.username if request.user.is_authenticated else 'anonymous'

                # create ticket
                ticket = Ticket(code=code,
                                subject=subject,
                                description=description,
                                modulo_compilato=json_data,
                                created_by=current_user,
                                input_module=modulo)

                # if ticket has been compiled by another user
                if compiled_by_user:
                    ticket.compiled_by = compiled_by_user
                    ticket.compiled = compiled_date

                # save ticket
                ticket.save()

                # compress content (default makes a check on length)
                ticket.compress_modulo_compilato()

                # log action
                logger.info('[{}] user {} created new ticket {}'
                            ' in category {}'.format(timezone.localtime(),
                                                     log_user,
                                                     ticket,
                                                     category))

                # save ticket attachments in ticket folder
                json_dict = json.loads(json_data)
                json_stored = get_as_dict(compiled_module_json=json_dict)
                _save_new_ticket_attachments(ticket=ticket,
                                             json_stored=json_stored,
                                             form=form,
                                             request_files=request.FILES)

                # assign ticket to the office
                ticket_assignment = TicketAssignment(ticket=ticket,
                                                     office=office)
                ticket_assignment.save()

                # log action
                logger.info('[{}] ticket {} assigned to '
                            '{} office'.format(timezone.localtime(),
                                               ticket,
                                               office))

                # if it's a notification ticket, take and close the ticket
                if category.is_notification:
                    _close_notification_ticket(ticket=ticket,
                                               user=current_user)
                                               # operator=random_office_operator,
                                               # ticket_assignment=ticket_assignment)

                else:
                    # category default tasks assigned to ticket (if present)
                    _assign_default_tasks_to_new_ticket(ticket=ticket,
                                                        category=category,
                                                        log_user=log_user)

                # send success message to user
                ticket_message = ticket.input_module.ticket_category.confirm_message_text or \
                                 settings.NEW_TICKET_CREATED_ALERT

                compiled_message = ticket_message.format(ticket.subject)

                # Protocol
                if category.protocol_required:
                    try:
                        protocol_struct_configuration = OrganizationalStructureWSArchiPro.get_active_protocol_configuration(struttura)
                        protocol_configuration = category.get_active_protocol_configuration()

                        response = download_ticket_pdf(request=request,
                                                       ticket_id=ticket.code).content

                        protocol_number = ticket_protocol(structure_configuration=protocol_struct_configuration,
                                                          configuration=protocol_configuration,
                                                          user=current_user,
                                                          subject=ticket.subject,
                                                          file_name=ticket.code,
                                                          response=response,
                                                          attachments_folder=ticket.get_folder(),
                                                          attachments_dict=ticket.get_allegati_dict())
                        # set protocol data in ticket
                        ticket.protocol_number = protocol_number
                        ticket.protocol_date = timezone.localtime()
                        ticket.save(update_fields=['protocol_number',
                                                   'protocol_date'])
                        messages.add_message(request, messages.SUCCESS,
                                             _("Richiesta protocollata "
                                               "correttamente: n. <b>{}/{}</b>"
                                               "").format(protocol_number,
                                                          timezone.localtime().year))
                    # if protocol fails
                    # raise Exception and do some operations
                    except Exception as e:
                        # log protocol fails
                        logger.error('[{}] user {} protocol for ticket {} '
                                     'failed: {}'
                                     ''.format(timezone.localtime(),
                                               log_user,
                                               ticket,
                                               e))
                        # delete attachments
                        # delete_directory(ticket.get_folder())

                        # delete assignment
                        # ticket_assignment.delete()
                        # delete ticket
                        # ticket.delete()
                        messages.add_message(request, messages.ERROR,
                                             _("<b>Errore protocollo</b>: {}").format(e))
                        messages.add_message(request, messages.INFO,
                                             _("<b>Attenzione</b>: la tua richiesta è stata "
                                               "comunque creata, nonostante "
                                               "la protocollazione sia fallita."))
                        # stop all other operations and come back to form
                        # return render(request, template, d)
                # end Protocol

                if category.protocol_required and ticket.protocol_number or not category.protocol_required:
                    messages.add_message(request, messages.SUCCESS, compiled_message)

                # if office operators must receive notification email
                if category.receive_email:
                    # Send mail to ticket
                    structure = category.organizational_structure
                    mail_params = {'hostname': settings.HOSTNAME,
                                   'ticket_url': request.build_absolute_uri(reverse('uni_ticket:manage_ticket_url_detail',
                                                                                     kwargs={'ticket_id': ticket.code,
                                                                                             'structure_slug': structure.slug})),
                                   'ticket_subject': ticket.subject,
                                   'ticket_description': ticket.description,
                                   'ticket_user': ticket.created_by,
                                   'destination_office': category.organizational_office,
                                  }
                    _send_new_ticket_mail_to_operators(request=request,
                                                       ticket=ticket,
                                                       category=category,
                                                       message_template=settings.NEW_TICKET_CREATED_EMPLOYEE_BODY,
                                                       mail_params=mail_params)

                # if user is authenticated send mail and redirect to ticket page
                if request.user.is_authenticated:
                    # Send mail to ticket owner
                    mail_params = {'hostname': settings.HOSTNAME,
                                   'user': request.user,
                                   'ticket': ticket.code,
                                   'ticket_subject': subject,
                                   'url': request.build_absolute_uri(reverse('uni_ticket:ticket_detail',
                                                                     kwargs={'ticket_id': ticket.code})),
                                    'added_text': compiled_message
                                  }

                    # m_subject = _('{} - {}'.format(settings.HOSTNAME,
                                                   # compiled_message))
                    # m_subject = m_subject[:80] + (m_subject[80:] and '...')
                    m_subject = _('{} - richiesta {} '
                                  'creata con successo'
                                  '').format(settings.HOSTNAME,
                                             ticket)

                    send_custom_mail(subject=m_subject,
                                     recipients=ticket.get_owners(),
                                     body=settings.NEW_TICKET_CREATED,
                                     params=mail_params)
                    # END Send mail to ticket owner

                    return redirect('uni_ticket:ticket_detail',
                                    ticket_id=ticket.code)
                else:
                    return redirect('uni_ticket:add_new_ticket',
                                    structure_slug=structure_slug,
                                    category_slug=category_slug)
        else: # pragma: no cover
            for k,v in get_labeled_errors(form).items():
                messages.add_message(request, messages.ERROR,
                                     "<b>{}</b>: {}".format(k, strip_tags(v)))
    return render(request, template, d)

@login_required
def dashboard(request):
    """
    Dashboard of user, with tickets list

    :return: render
    """

    # Ci pensa datatables a popolare la tabella
    title =_("Pannello di controllo")
    sub_title = _("Gestisci le tue richieste o creane di nuove")
    template = "user/dashboard.html"
    tickets = Ticket.objects.filter(Q(created_by=request.user) | \
                                    Q(compiled_by=request.user))
    not_closed = tickets.filter(is_closed=False)
    # unassigned = []
    # opened = []
    unassigned = 0
    opened = 0
    for nc in not_closed:
        if nc.has_been_taken():
            # opened.append(nc)
            opened += 1
        else:
            # unassigned.append(nc)
            unassigned += 1
    # chiusi = tickets.filter(is_closed=True)
    chiusi = tickets.filter(is_closed=True).count()

    messages = TicketReply.get_unread_messages_count(tickets=tickets,
                                                     by_operator=True)

    d = {'priority_levels': settings.PRIORITY_LEVELS,
         'sub_title': sub_title,
         'ticket_aperti': opened,
         'ticket_chiusi': chiusi,
         'ticket_messages': messages,
         'ticket_non_gestiti': unassigned,
         'title': title,}

    return render(request, template, d)

@login_required
@is_the_owner
@ticket_is_not_taken_and_not_closed
def ticket_edit(request, ticket_id):
    """
    Edit ticket details while it is unassigned
    Note: formset validation is in widget (._fill_body method)

    :type ticket_id: String

    :param ticket_id: ticket code

    :return: render
    """
    ticket = get_object_or_404(Ticket, code=ticket_id)

    if ticket.protocol_number:
        messages.add_message(request, messages.ERROR,
                             _("Impossibile modificare una richiesta protocollata"))
        return redirect('uni_ticket:ticket_detail',
                        ticket_id=ticket.code)

    # deny action if user is not the owner but has compiled only
    if not request.user == ticket.created_by:
        messages.add_message(request, messages.ERROR,
                             settings.TICKET_SHARING_USER_ERROR_MESSAGE.format(ticket.created_by))
        return redirect('uni_ticket:ticket_detail',
                        ticket_id=ticket.code)

    categoria = ticket.input_module.ticket_category
    title = _("Modifica ticket")
    sub_title = ticket
    allegati = ticket.get_allegati_dict()
    path_allegati = get_path(ticket.get_folder())
    form = ticket.compiled_form(files=None, remove_filefields=allegati)
    form_allegati = ticket.compiled_form(files=None,
                                         remove_filefields=False,
                                         remove_datafields=True)
    template = "user/ticket_edit.html"
    d = {'allegati': allegati,
         'categoria': categoria,
         'form': form,
         'form_allegati': form_allegati,
         'path_allegati': path_allegati,
         'sub_title': sub_title,
         'ticket': ticket,
         'title': title,}
    if request.method == 'POST':
        fields_to_pop = [settings.TICKET_CONDITIONS_FIELD_ID]
        json_post = get_POST_as_json(request=request,
                                     fields_to_pop=fields_to_pop)
        json_response=json.loads(json_post)
        # Costruisco il form con il json dei dati inviati e tutti gli allegati
        # json_response[settings.ATTACHMENTS_DICT_PREFIX]=allegati
        # rimuovo solo gli allegati che sono stati già inseriti
        modulo = ticket.get_form_module()
        form = modulo.get_form(data=json_response,
                               files=request.FILES,
                               remove_filefields=allegati)

        d['form'] = form

        if form.is_valid():
            if request.FILES:
                json_response[settings.ATTACHMENTS_DICT_PREFIX] = allegati
                json_stored = get_as_dict(compiled_module_json=json_response)
                _save_new_ticket_attachments(ticket=ticket,
                                             json_stored=json_stored,
                                             form=form,
                                             request_files=request.FILES)
            elif allegati:
                # If data aren't updated (the same as the original)
                json_response[settings.ATTACHMENTS_DICT_PREFIX] = allegati

            # save module
            ticket.save_data(form.cleaned_data[settings.TICKET_SUBJECT_ID],
                             form.cleaned_data[settings.TICKET_DESCRIPTION_ID],
                             json_response)

            # compress content (default makes a check on length)
            ticket.compress_modulo_compilato()

            # update modified date
            ticket.update_log(user=request.user,
                              note=_("Ticket modificato"))

            # log action
            logger.info('[{}] user {} edited ticket {}'.format(timezone.localtime(),
                                                               request.user,
                                                               ticket))

            # Attach a message to redirect action
            messages.add_message(request, messages.SUCCESS,
                                 _("Modifica effettuata con successo"))
            return redirect('uni_ticket:ticket_edit', ticket_id=ticket_id)
        else: # pragma: no cover
            for k,v in get_labeled_errors(form).items():
                messages.add_message(request, messages.ERROR,
                                     "<b>{}</b>: {}".format(k, strip_tags(v)))

    return render(request, template, d)

@login_required
@is_the_owner
@ticket_is_not_taken_and_not_closed
def delete_my_attachment(request, ticket_id, attachment):
    """
    Delete ticket attachment while it is unassigned
    Note: it must be called by a dialogbox with user confirmation

    :type ticket_id: String
    :type attachment: String

    :param ticket_id: ticket code
    :param attachment: attachment name

    :return: redirect
    """
    ticket = get_object_or_404(Ticket, code=ticket_id)
    json_dict = ticket.get_modulo_compilato()
    ticket_details = get_as_dict(compiled_module_json=json_dict)
    nome_file = ticket_details[settings.ATTACHMENTS_DICT_PREFIX][attachment]

    # Rimuove il riferimento all'allegato dalla base dati
    del ticket_details[settings.ATTACHMENTS_DICT_PREFIX][attachment]
    path_allegato = get_path(ticket.get_folder())

    # Rimuove l'allegato dal disco
    delete_file(file_name=nome_file, path=path_allegato)

    # log action
    logger.info('[{}] user {} deleted file {}'.format(timezone.localtime(),
                                                      request.user.username,
                                                      path_allegato))

    set_as_dict(ticket, ticket_details)
    allegati = ticket.get_allegati_dict(ticket_dict=ticket_details)
    ticket.update_log(user=request.user,
                      note=_("Elimina allegato"))

    # log action
    logger.info('[{}] user {} deleted attachment '
                '{} for ticket {}'.format(timezone.localtime(),
                                          request.user.username,
                                          nome_file,
                                          ticket))

    messages.add_message(request, messages.SUCCESS,
                         _("Allegato eliminato correttamente"))
    return redirect('uni_ticket:ticket_edit', ticket_id=ticket_id)

@login_required
@is_the_owner
@ticket_is_not_taken_and_not_closed
def ticket_delete(request, ticket_id):
    """
    Delete ticket while it is unassigned
    Note: it must be called by a dialogbox with user confirmation

    :type ticket_id: String

    :param ticket_id: ticket code

    :return: redirect
    """
    ticket = get_object_or_404(Ticket, code=ticket_id)

    if ticket.protocol_number:
        messages.add_message(request, messages.ERROR,
                             _("Impossibile eliminare una richiesta protocollata"))
        return redirect('uni_ticket:ticket_detail',
                        ticket_id=ticket.code)

    # deny action if user is not the owner but has compiled only
    if not request.user == ticket.created_by:
        messages.add_message(request, messages.ERROR,
                             settings.TICKET_SHARING_USER_ERROR_MESSAGE.format(ticket.created_by))
        return redirect('uni_ticket:ticket_detail',
                        ticket_id=ticket.code)

    ticket_assignment = TicketAssignment.objects.filter(ticket=ticket).first()

    # log action
    logger.info('[{}] ticket {} assignment'
                ' to office {}'
                ' has been deleted'
                ' by user {}'.format(timezone.localtime(),
                                     ticket,
                                     ticket_assignment.office,
                                     request.user))

    ticket_assignment.delete()

    # Send mail to ticket owner
    mail_params = {'hostname': settings.HOSTNAME,
                   'user': request.user,
                   'status': _("eliminato"),
                   'ticket': ticket
                  }
    m_subject = _('{} - richiesta {} eliminata'.format(settings.HOSTNAME,
                                                    ticket))

    send_custom_mail(subject=m_subject,
                     recipients=ticket.get_owners(),
                     body=settings.TICKET_DELETED,
                     params=mail_params)
    # END Send mail to ticket owner

    ticket.delete()

    # log action
    logger.info('[{}] user {} deleted ticket {}'.format(timezone.localtime(),
                                                        request.user,
                                                        ticket))

    messages.add_message(request, messages.SUCCESS,
                         _("Ticket {} eliminato correttamente".format(ticket.code)))
    return redirect('uni_ticket:user_unassigned_ticket')

# @login_required
# @is_the_owner
# decorators in urls.py (print view call this view but with different decorators)
def ticket_detail(request, ticket_id, template='user/ticket_detail.html'):
    """
    Shows ticket details

    :type ticket_id: String
    :type template: String

    :param ticket_id: ticket code
    :param attachment: template to user (can change if specified)

    :return: render
    """
    ticket = get_object_or_404(Ticket, code=ticket_id)
    modulo_compilato = ticket.get_modulo_compilato()
    ticket_details = get_as_dict(compiled_module_json=modulo_compilato,
                                 allegati=False,
                                 formset_management=False)
    allegati = ticket.get_allegati_dict()
    path_allegati = get_path(ticket.get_folder())
    ticket_form = ticket.input_module.get_form(files=allegati,
                                               remove_filefields=False)
    priority = ticket.get_priority()

    ticket_logs = LogEntry.objects.filter(content_type_id=ContentType.objects.get_for_model(ticket).pk,
                                          object_id=ticket.pk)
    ticket_replies = TicketReply.objects.filter(ticket=ticket)
    ticket_task = Task.objects.filter(ticket=ticket)
    ticket_dependences = ticket.get_dependences()
    title = ticket.subject
    sub_title = ticket.code
    assigned_to = []
    ticket_assignments = TicketAssignment.objects.filter(ticket=ticket)

    category_conditions = ticket.input_module.ticket_category.get_conditions(is_printable=True)

    d={'allegati': allegati,
       'category_conditions': category_conditions,
       'dependences': ticket_dependences,
       'details': ticket_details,
       'path_allegati': path_allegati,
       'priority': priority,
       'sub_title': sub_title,
       'ticket': ticket,
       'ticket_assignments': ticket_assignments,
       'ticket_form': ticket_form,
       'logs': ticket_logs,
       'ticket_task': ticket_task,
       'title': title,}
    template = template
    return render(request, template, d)

@login_required
def ticket_url(request):
    """
    Fake URL to build datatables ticket details link on click (href)
    """
    return custom_message(request, _("Permesso negato"))

@login_required
@is_the_owner
def ticket_message(request, ticket_id):
    """
    Ticket messages page

    :param ticket_id: String

    :type ticket_id: ticket code

    :return: render
    """
    ticket = get_object_or_404(Ticket, code=ticket_id)
    title = _("Messaggi")
    # Conversazione utente-operatori
    ticket_replies = TicketReply.objects.filter(ticket=ticket)
    form = ReplyForm()
    # if ticket.is_open():
    agent_replies = ticket_replies.filter(read_by=None).exclude(structure=None)
    if request.user == ticket.created_by:
        for reply in agent_replies:
            reply.read_by = request.user
            reply.read_date = timezone.localtime()
            reply.save(update_fields = ['read_by', 'read_date'])

    if request.method == 'POST':

        # deny action if user is not the owner but has compiled only
        # if not request.user == ticket.created_by:
            # messages.add_message(request, messages.ERROR,
                                 # settings.TICKET_SHARING_USER_ERROR_MESSAGE.format(ticket.created_by))
            # return redirect('uni_ticket:ticket_message',
                            # ticket_id=ticket_id)

        if not ticket.is_open():
            # log action
            logger.error('[{}] user {} tried to submit'
                         ' a message for the not opened ticket {}'.format(timezone.localtime(),
                                                                         request.user,
                                                                         ticket))
            return custom_message(request, _("La richiesta non è modificabile"))
        form = ReplyForm(request.POST, request.FILES)
        if form.is_valid():
            ticket_reply = form.save(commit=False)
            ticket_reply.ticket = ticket
            ticket_reply.owner = request.user
            ticket_reply.save()

            # log action
            logger.info('[{}] user {} submitted a message'
                        ' for ticket {}'.format(timezone.localtime(),
                                                request.user,
                                                ticket))

            # add to ticket log history
            log_msg = _("Nuovo messaggio (da utente). Oggetto: {} / "
                        "Testo: {}").format(ticket_reply.subject,
                                            ticket_reply.text)
            ticket.update_log(request.user, note=log_msg, send_mail=False)

            # Send mail to ticket owner
            mail_params = {'hostname': settings.HOSTNAME,
                           'status': _("inviato"),
                           'message_subject': ticket_reply.subject,
                           'message_text': ticket_reply.text,
                           'ticket': ticket,
                           'user': request.user,
                           'url': request.build_absolute_uri(reverse('uni_ticket:ticket_message',
                                                             kwargs={'ticket_id': ticket.code}))
                          }
            m_subject = _('{} - richiesta {} messaggio inviato'.format(settings.HOSTNAME,
                                                                    ticket))
            send_custom_mail(subject=m_subject,
                             recipients=[request.user],
                             body=settings.USER_TICKET_MESSAGE,
                             params=mail_params)
            # END Send mail to ticket owner

            # Send email to operators (if category flag is checked)
            category = ticket.input_module.ticket_category
            return_url = request.build_absolute_uri(reverse('uni_ticket:manage_ticket_message_url',
                                                             kwargs={'ticket_id': ticket.code,
                                                                     'structure_slug': category.organizational_structure.slug}))
            if category.receive_email:
                # Send mail to ticket
                mail_params = {'hostname': settings.HOSTNAME,
                               'url': return_url,
                               'message_subject': ticket_reply.subject,
                               'message_text': ticket_reply.text,
                               'ticket': ticket,
                              }
                _send_new_ticket_mail_to_operators(request=request,
                                                   ticket=ticket,
                                                   category=category,
                                                   message_template=settings.NEW_MESSAGE_RECEIVED_EMPLOYEE_BODY,
                                                   mail_params=mail_params)
            # END Send email to operators

            messages.add_message(request, messages.SUCCESS,
                                 _("Messaggio inviato con successo"))
            return redirect('uni_ticket:ticket_message',
                            ticket_id=ticket_id)
        else: # pragma: no cover
            for k,v in get_labeled_errors(form).items():
                messages.add_message(request, messages.ERROR,
                                     "<b>{}</b>: {}".format(k, strip_tags(v)))
    d={'form': form,
       'sub_title': ticket.__str__(),
       'sub_title_2': ticket.description,
       'ticket': ticket,
       'ticket_replies': ticket_replies,
       'title': title,}
    template='user/ticket_assistance.html'
    return render(request, template, d)

@login_required
@is_the_owner
def task_detail(request, ticket_id, task_id): # pragma: no cover
    """
    Task details page

    :param ticket_id: String
    :param task_id: String

    :type ticket_id: ticket code
    :type task_id: task code

    :return: render
    """
    ticket = get_object_or_404(Ticket, code=ticket_id)
    task = get_object_or_404(Task, code=task_id, ticket=ticket)
    if not task.is_public:
        return custom_message(request, _("Attività riservata agli operatori"))

    priority = task.get_priority()
    title = _("Dettaglio task")
    d={'priority': priority,
       'sub_title': task,
       'task': task,
       'title': title}
    template = "user/task_detail.html"
    return render(request, template, d)

@login_required
@is_the_owner
def ticket_close(request, ticket_id):
    """
    Ticket closing by owner user

    :param ticket_id: String

    :type ticket_id: ticket code

    :return: render
    """
    ticket = get_object_or_404(Ticket, code=ticket_id)

    if ticket.is_closed:
        # log action
        logger.error('[{}] user {} tried to close '
                     ' the already closed ticket {}'.format(timezone.localtime(),
                                                            request.user,
                                                            ticket))

        return custom_message(request, _("La richiesta è già chiusa!"))

    # deny action if user is not the owner but has compiled only
    if not request.user == ticket.created_by:
        messages.add_message(request, messages.ERROR,
                             settings.TICKET_SHARING_USER_ERROR_MESSAGE.format(ticket.created_by))
        return redirect('uni_ticket:ticket_detail',
                        ticket_id=ticket.code)

    title = _('Chiusura della richiesta')
    sub_title = ticket
    form = BaseTicketCloseForm()
    if request.method=='POST':
        form = BaseTicketCloseForm(request.POST)
        if form.is_valid():
            motivazione = form.cleaned_data['note']
            # closing_status = form.cleaned_data['status']
            ticket.is_closed = True
            ticket.closing_reason = motivazione
            # ticket.closing_status = closing_status
            ticket.closed_date = timezone.localtime()
            ticket.save(update_fields = ['is_closed',
                                         'closing_reason',
                                         # 'closing_status',
                                         'closed_date'])
            ticket.update_log(user=request.user,
                              note=_("Chiusura richiesta da utente "
                                     "proprietario: {}").format(motivazione))
            messages.add_message(request, messages.SUCCESS,
                                 _("Richiesta {} chiusa correttamente"
                                   "").format(ticket))

            # log action
            logger.info('[{}] user {} closed ticket {}'.format(timezone.localtime(),
                                                               request.user,
                                                               ticket))

            return redirect('uni_ticket:ticket_detail', ticket.code)
        else: # pragma: no cover
            for k,v in get_labeled_errors(form).items():
                messages.add_message(request, messages.ERROR,
                                     "<b>{}</b>: {}".format(k, strip_tags(v)))

    template = "user/ticket_close.html"
    d = {'form': form,
         'sub_title': sub_title,
         'ticket': ticket,
         'title': title,}
    return render(request, template, d)

@login_required
@is_the_owner
def ticket_reopen(request, ticket_id):
    """
    Reopen ticket

    :type ticket_id: String

    :param ticket_id: ticket code

    :return: redirect
    """
    ticket = get_object_or_404(Ticket, code=ticket_id)

    # Se il ticket non è chiuso blocca
    if not ticket.is_closed:
        logger.error('[{}] {} tried to reopen not closed ticket {} '
                     ''.format(timezone.localtime(), request.user, ticket))
        return custom_message(request, _("La richiesta non è stata chiusa"))

    if ticket.closed_by:
        logger.error('[{}] {} tried to reopen ticket {} '
                     ' closed by operator'.format(timezone.localtime(),
                                                  request.user,
                                                  ticket))
        return custom_message(request, _("La richiesta è stata chiusa "
                                         "da un operatore e non può "
                                         "essere riaperta"))

    if ticket.is_notification:
        logger.error('[{}] {} tried to reopen notification ticket {} '
                     ''.format(timezone.localtime(), request.user, ticket))
        return custom_message(request, _("La richiesta è di tipo "
                                         "notifica e non può essere "
                                         "riaperta"))

    ticket.is_closed = False
    ticket.save(update_fields = ['is_closed'])

    msg = _("Riapertura richiesta {} da utente proprietario").format(ticket)
    # log action
    logger.error('[{}] {} reopened ticket {}'.format(timezone.localtime(),
                                                     request.user,
                                                     ticket))

    ticket.update_log(user=request.user, note=msg)
    messages.add_message(request, messages.SUCCESS,
                         _("Richiesta {} riaperta correttamente".format(ticket)))
    return redirect('uni_ticket:ticket_detail',ticket_id=ticket_id)

@login_required
def chat_new_preload(request, structure_slug=None): # pragma: no cover
    """
    Choose the OrganizationalStructure and the category of the ticket

    :type structure_slug: String

    :param structure_slug: slug of structure

    :return: render
    """
    strutture = OrganizationalStructure.objects.filter(is_active=True)
    template = "user/new_chat_preload.html"
    title = _("Avvia chat con un operatore")
    sub_title = _("Seleziona la struttura")
    if structure_slug:
        struttura = get_object_or_404(OrganizationalStructure,
                                      slug=structure_slug,
                                      is_active=True)
        sub_title = struttura
    d = {'structure_slug': structure_slug,
         'strutture': strutture,
         'sub_title': sub_title,
         'title': title,}
    return render(request, template, d)

@login_required
def ticket_clone(request, ticket_id):
    main_ticket = get_object_or_404(Ticket,
                                    code=ticket_id,
                                    created_by=request.user)
    # if ticket is not closed and owner has closed it
    # if not main_ticket.is_closed:
       # return custom_message(request, _("Operazione non permessa. "
                                        # "La richiesta è ancora attiva"))

    # if ticket module is out of date
    if not main_ticket.input_module.is_active:
           return custom_message(request, _("Il modulo che stai cercando "
                                            "di usare non è più attivo."))

    category = main_ticket.input_module.ticket_category
    form_data = main_ticket.get_modulo_compilato()

    form_data.update({settings.TICKET_INPUT_MODULE_NAME: main_ticket.input_module.pk})
    form_data.update({settings.TICKET_SUBJECT_ID: main_ticket.subject})
    form_data.update({settings.TICKET_DESCRIPTION_ID: main_ticket.description})

    # build encrypted url param with form data
    encrypted_data = encrypt_to_jwe(json.dumps(form_data).encode())
    base_url = reverse('uni_ticket:add_new_ticket',
                       kwargs={'structure_slug': category.organizational_structure.slug,
                               'category_slug': category.slug})
    return HttpResponseRedirect(base_url + "?import={}".format(encrypted_data))

@login_required
@has_access_to_ticket
def ticket_detail_print(request, ticket_id, ticket): # pragma: no cover
    """
    Displays ticket print version

    :type ticket_id: String
    :type ticket: Ticket (from @has_access_to_ticket)

    :param ticket_id: ticket code
    :param ticket: ticket object (from @has_access_to_ticket)

    :return: view response
    """
    response = ticket_detail(request,
                             ticket_id=ticket_id,
                             template='ticket_detail_print.html')
    return response

@login_required
@has_access_to_ticket
def download_ticket_pdf(request, ticket_id, ticket): # pragma: no cover
    response = ticket_detail(request,
                             ticket_id=ticket_id,
                             template='ticket_detail_print_pdf.html')

    # file names
    pdf_fname = '{}.pdf'.format(ticket.code)

    # get PDF

    # no need to merge if not attachments to manage :)
    return response_as_pdf(response, pdf_fname)

    #
    #
    #
    # if we want to manage attachments
    # we have to merge them in the main file (but only pdf!)
    #
    #
    #

    # pdf_path = settings.TMP_DIR + os.path.sep + pdf_fname
    # main_pdf_file = response_as_pdf(response, pdf_fname).content
    # merger = PdfFileMerger(strict=False)
    # main_pdf_file = BytesIO(main_pdf_file)
    # merger.append(main_pdf_file)

    # try:
        # #append attachments

        # #not PDF files raise Exception!

        # for k,v in ticket.get_allegati_dict().items():
            # path = '{}/{}/{}'.format(settings.MEDIA_ROOT,
                                     # ticket.get_folder(),
                                     # v)
            # merger.append(path)

        # #end append attachments
        # merger.write(pdf_path)

        # #put all in response
        # f = open(pdf_path, 'rb')
        # response = HttpResponse(f.read(), content_type='application/pdf')
        # response['Content-Disposition'] = 'inline; filename=' + pdf_fname
    # except Exception as e:
        # logger.error('[{}] user {} tried to download pdf version '
                     # ' of ticket {} but got an error'
                     # ''.format(timezone.localtime(),
                               # request.user,
                               # ticket))

        # #if attachments!
        # #json_dict = json.loads(ticket.modulo_compilato)
        # #ticket_dict = get_as_dict(json_dict)
        # #return custom_message(request,
                              ## _("Sei incorso in un errore relativo alla interpretazione "
                                ## "dei file PDF da te immessi come allegato. "
                                ## "Nello specifico: '{}' presenta delle anomalie di formato. "
                                ## "Questo è dovuto al processo di produzione "
                                ## "del PDF. E' necessario ricreare il PDF "
                                ## "con una procedura differente da quella "
                                ## "precedenemente utilizzata oppure, più "
                                ## "semplicemente, ristampare il PDF come file, "
                                ## "rimuovere il vecchio allegato dal modulo inserito "
                                ## "e caricare il nuovo appena ristampato/riconvertito."
                                ## ).format(ticket_dict.get('allegati')))
        # return custom_message(request,
                              # _("Errore nella generazione del file PDF"))
    ## clean
    # f.close()
    # main_pdf_file.close()
    # os.remove(pdf_path)
    # return response
