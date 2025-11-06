from copy import deepcopy
import os
import json
import logging
import re
import shutil
from typing import Union

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.mail import send_mail
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.views import View
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.html import strip_tags
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST


from django_form_builder.utils import (
    get_as_dict,
    get_labeled_errors,
    # get_POST_as_json,
    set_as_dict,
)
from organizational_area.models import (
    OrganizationalStructure,
    OrganizationalStructureOfficeEmployee,
)

from uni_ticket.decorators import *
from uni_ticket.forms import *
from uni_ticket.jwts import *
from uni_ticket.models import *
from uni_ticket.pdf_utils import response_as_pdf
from uni_ticket.protocol_utils import ticket_protocol
from uni_ticket.settings import (
    NEW_MESSAGE_RECEIVED_EMPLOYEE_BODY,
    NEW_TICKET_CREATED,
    NEW_TICKET_CREATED_EMPLOYEE_BODY,
    OPERATOR_PREFIX,
    TICKET_CAPTCHA_HIDDEN_ID,
    TICKET_CAPTCHA_ID,
    TICKET_COMPILED_BY_USER_NAME,
    TICKET_COMPILED_CREATION_DATE,
    TICKET_COMPILED_ONE_TIME_FLAG,
    TICKET_CONDITIONS_FIELD_ID,
    TICKET_CREATE_BUTTON_NAME,
    TICKET_DELETED,
    TICKET_GENERATE_URL_BUTTON_NAME,
    TICKET_INPUT_MODULE_NAME,
    TICKET_SHARING_USER_ERROR_MESSAGE,
    UNAVAILABLE_TICKET_CATEGORY,
    USER_TICKET_MESSAGE
)
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
        ticket_task.is_printable = task.is_printable
        # ~ ticket_task.created_by = task.created_by
        ticket_task.created_by = None
        ticket_task.code = uuid_code()
        ticket_task.attachment = task.attachment
        ticket_task.ordering = task.ordering
        ticket_task.save()

        # copy category task attachments in ticket task folder
        if task.attachment:
            source = "{}/{}".format(settings.MEDIA_ROOT, task.get_folder())
            destination = "{}/{}".format(settings.MEDIA_ROOT,
                                         ticket_task.get_folder())
            try:
                if os.path.exists(source):
                    shutil.copytree(source, destination)
            except Exception:
                logger.error(
                    "[{}] {} try to copy not existent folder {}"
                    "".format(timezone.localtime(), log_user, source)
                )


# close ticket as soon as opened if it's a notification ticket


def _close_notification_ticket(ticket, user):  # operator, ticket_assignment):
    # close ticket
    ticket.is_notification = True
    ticket.is_closed = True
    ticket.closed_date = timezone.localtime()
    # ticket.closed_by = user
    # default closing status: success
    ticket.closing_status = 1
    ticket.save(
        update_fields=["is_notification", "is_closed",
                       "closed_date", "closing_status"]
    )
    # 'closed_by'])

    # assign to an operator
    # ticket_assignment.taken_date = timezone.localtime()
    # ticket_assignment.taken_by = operator
    # ticket_assignment.save(update_fields=['taken_date', 'taken_by'])


# save attachments of new ticket


def _save_new_ticket_attachments(ticket, json_stored, form, request_files):
    if request_files:
        if not json_stored.get(settings.ATTACHMENTS_DICT_PREFIX):
            json_stored[settings.ATTACHMENTS_DICT_PREFIX] = {}
        path_allegati = get_path(ticket.get_folder())
        attach_key = ""
        attach_value = ""

        for key, value in request_files.items():
            formset_regex = re.match(settings.FORMSET_FULL_REGEX, key)
            if formset_regex:
                formset_field = form.fields[formset_regex["field_name"]]
                if formset_field.is_formset:
                    sub_field_name = formset_regex["name"]
                    index = formset_regex["index"]
                    formset_data = formset_field.widget.formset.forms[
                        int(index)
                    ].cleaned_data
                    attach_key = formset_data[sub_field_name]
                    attach_value = attach_key._name
            else:
                attach_key = form.cleaned_data[key]
                attach_value = attach_key._name

            save_file(attach_key, path_allegati, attach_value)
            json_stored[settings.ATTACHMENTS_DICT_PREFIX][key] = attach_value

            # log action
            logger.info(
                "[{}] attachment {} saved in {}".format(
                    timezone.localtime(), attach_key, path_allegati
                )
            )

        set_as_dict(ticket, json_stored)


def get_structures_by_request(request, structure_slug):
    try:
        structure = get_object_or_404(
            OrganizationalStructure, pk=structure_slug, is_active=True
        )
    except Exception:
        structure = get_object_or_404(
            OrganizationalStructure, slug=structure_slug, is_active=True
        )

    alerts = OrganizationalStructureAlert.objects.filter(
        organizational_structure=structure, is_active=True
    )
    # disable_expired_items(alerts)
    active_alerts = [i for i in alerts if i.is_published()]

    categorie = TicketCategory.objects.filter(
        organizational_structure=structure,
        is_hidden=False,
        is_active=True
    )

    # disable_expired_items(categorie)
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
        categorie = categorie.filter(
            Q(allow_employee=True) | Q(
                allow_user=True) | Q(allow_guest=True)
        )
    elif is_employee:
        categorie = categorie.filter(
            Q(allow_employee=True) | Q(allow_guest=True))
    elif is_user:
        categorie = categorie.filter(
            Q(allow_user=True) | Q(allow_guest=True))
    else:
        categorie = categorie.filter(allow_guest=True)

    sub_title = _("Seleziona la Categoria")
    return {
        "alerts": active_alerts,
        "categorie": categorie,
        "chosen_structure": structure,
        "sub_title": sub_title,
    }


@login_required
def ticket_new_preload(request, structure_slug:str = None):
    """
    Choose the OrganizationalStructure and the category of the ticket

    :type structure_slug: String

    :param structure_slug: slug of structure

    :return: render
    """
    template = "user/new_ticket_preload.html"

    if Ticket.number_limit_reached_by_user(request.user):
        messages.add_message(
            request,
            messages.ERROR,
            _(
                "Hai raggiunto il limite massimo giornaliero"
                " di richieste: <b>{}</b>"
                ""
            ).format(MAX_DAILY_TICKET_PER_USER),
        )
        return redirect(reverse("uni_ticket:user_dashboard"))

    d = {
        "alerts": [],
        "categorie": None,
        "chosen_structure": None,
        "strutture": OrganizationalStructure.objects.filter(is_active=True),
        "sub_title": _("Seleziona la struttura"),
        "title": _("Effettua una nuova richiesta"),
    }

    if structure_slug:
        _d = get_structures_by_request(request, structure_slug)
        d.update(_d)

    return render(request, template, base_context(d))


class TicketAddNew(View):

    compiled_by_user = None
    compiled_date = None

    template = "user/ticket_add_new.html"

    def get_assets(self, structure_slug, category_slug) -> None:
        # get structure by pk or by slug
        try:
            self.struttura = get_object_or_404(
                OrganizationalStructure, pk=structure_slug, is_active=True
            )
        except Exception:
            self.struttura = get_object_or_404(
                OrganizationalStructure, slug=structure_slug, is_active=True
            )
        # get category by pk or by slug
        try:
            self.category = get_object_or_404(
                TicketCategory, pk=category_slug, organizational_structure=self.struttura
            )
        except Exception:
            self.category = get_object_or_404(
                TicketCategory, slug=category_slug, organizational_structure=self.struttura
            )
        self.sub_title = (
            self.category.description if self.category.description else _(
                "Compila i campi richiesti")
        )
        self.title = self.category

    def get_modulo_and_form(self) -> None:
        # if there is an encrypted token with ticket params in URL
        if self.request.GET.get("import"):
            CompiledTicket.clear()
            encoded_data = self.request.GET["import"]
            try:
                compiled_ticket = get_object_or_404(CompiledTicket, url_path=encoded_data)
            except Exception:
                return custom_message(self.request, _("Il ticket precompilato è scaduto"))
            try:
                # decrypt and get imported form content
                imported_data = json.loads(decrypt_from_jwe(compiled_ticket.content))
                # one time
                if compiled_ticket.one_time:
                    compiled_ticket.delete()
            except Exception:
                return custom_message(self.request, _("Dati da importare non consistenti."))
            # get input_module id from imported data
            module_id = imported_data.get(TICKET_INPUT_MODULE_NAME)
            if not module_id:
                return custom_message(
                    self.request,
                    _("Dati da importare non consistenti. Modulo di input mancante"),
                )
            self.modulo = get_object_or_404(
                TicketCategoryModule, ticket_category=self.category, pk=module_id
            )
            # get user that compiled module (if exists)
            compiled_by_user_id = imported_data.get(TICKET_COMPILED_BY_USER_NAME)
            if compiled_by_user_id:
                self.compiled_by_user = (
                    get_user_model().objects.filter(pk=compiled_by_user_id[1]).first()
                )
                self.compiled_date = (
                    parse_datetime(imported_data.get(
                        TICKET_COMPILED_CREATION_DATE))
                    if imported_data.get(TICKET_COMPILED_CREATION_DATE)
                    else timezone.localtime()
                )
            # get compiled form
            self.form = self.modulo.get_form(
                data=imported_data, show_conditions=True, current_user=self.request.user
            )
        else:
            self.modulo = get_object_or_404(
                TicketCategoryModule, ticket_category=self.category, is_active=True
            )
            self.form = self.modulo.get_form(
                show_conditions=True, current_user=self.request.user
            )
        self.clausole_categoria = self.category.get_conditions()

    def protocolla_ticket(self) -> None:
        try:
            protocol_struct_configuration = OrganizationalStructureWSProtocollo.get_active_protocol_configuration(
                self.struttura
            )
            protocol_configuration = (
                self.category.get_active_protocol_configuration()
            )

            response = download_ticket_pdf(
                request=self.request,
                ticket_id=self.ticket.code,
                # TODO - get from settings and not hardcode constants in the code
                template="ticket_detail_print_pdf_simplified.html",
            ).content

            protocol_response = ticket_protocol(
                structure_configuration=protocol_struct_configuration,
                configuration=protocol_configuration,
                user=self.current_user,
                subject=self.ticket.subject,
                file_name=self.ticket.code,
                response=response,
                attachments_folder=self.ticket.get_folder(),
                attachments_dict=self.ticket.get_allegati_dict(),
            )
            protocol_number = protocol_response["numero"]

            # set protocol data in ticket
            self.ticket.protocol_number = protocol_number
            self.ticket.protocol_date = timezone.localtime()
            self.ticket.save(update_fields=[
                        "protocol_number", "protocol_date"])
            messages.add_message(
                self.request,
                messages.SUCCESS,
                _(
                    "Richiesta protocollata "
                    "correttamente: n. <b>{}/{}</b>"
                    ""
                ).format(protocol_number, timezone.localtime().year),
            )
            if protocol_response.get("message"):
                messages.add_message(
                    self.request, messages.INFO, protocol_response["message"]
                )
        # if protocol fails
        # raise Exception and do some operations
        except Exception as e:
            # log protocol fails
            logger.error(
                "[{}] user {} protocol for ticket {} "
                "failed: {}"
                "".format(timezone.localtime(),
                          self.log_user, self.ticket, e)
            )

            # TODO: @francesco what to do with the following comments/legacy code?
            # delete attachments
            # delete_directory(ticket.get_folder())
            # delete assignment
            # ticket_assignment.delete()
            # delete ticket
            # ticket.delete()

            messages.add_message(
                self.request,
                messages.ERROR,
                _("<b>Errore protocollo</b>: {}").format(e),
            )
            messages.add_message(
                self.request,
                messages.INFO,
                _(
                    "<b>Attenzione</b>: la tua richiesta è stata "
                    "comunque creata, nonostante "
                    "la protocollazione sia fallita."
                ),
            )

    def deny_response(self):
        # if category is not active, return an error message
        if not self.category.is_published():
            unavailable_msg = self.category.not_available_message or UNAVAILABLE_TICKET_CATEGORY
            return custom_message(self.request, unavailable_msg, status=404)

        # TODO: not covered yet in the unit tests
        # if anonymous user and category only for logged users
        if not self.category.allow_anonymous and not self.request.user.is_authenticated:
            return redirect_after_login(self.request.get_full_path())

        # is user is authenticated
        if self.request.user.is_authenticated:

            # check ticket number limit
            if Ticket.number_limit_reached_by_user(self.request.user):
                messages.add_message(
                    self.request,
                    messages.ERROR,
                    _(
                        "Hai raggiunto il limite massimo giornaliero"
                        " di richieste: <b>{}</b>"
                    ).format(MAX_DAILY_TICKET_PER_USER)

                )
                return redirect("uni_ticket:user_dashboard")

            # check if user is allowed to access this category
            if not self.category.allowed_to_user(self.request.user):
                return custom_message(
                    self.request, _("Permesso negato a questa tipologia di utente.")
                )

            # check if user has already open a ticket of this category
            if not self.category.user_multiple_open_tickets and Ticket.existent_open_ticket(
                self.request.user, self.category
            ):
                return custom_message(
                    self.request,
                    _(
                        "Esistono già tue richieste aperte"
                        " di questa tipologia."
                        " Non puoi effettuarne di nuove"
                        " fino a quando queste non verranno chiuse"
                    ),
                )

            # checks if the user has exceeded the maximum ticket threshold of this category
            if self.category.max_requests_per_user and Ticket.objects.filter(
                created_by=self.request.user,
                input_module__ticket_category=self.category
            ).count() >= self.category.max_requests_per_user:
                return custom_message(
                    self.request,
                    _(
                        "Non è possibile aprire ulteriori richieste"
                        " per questa tipologia."
                    ),
                )

    def get(self, request, structure_slug, category_slug, api:bool = False):
        """
        Create the ticket

        :type structure_slug: String
        :type category_slug: String

        :param structure_slug: slug of structure
        :param category_slug: slug of category

        :return: render
        """
        self.get_assets(structure_slug, category_slug)
        deny_response = self.deny_response()
        if deny_response:
            return deny_response

        # user that compiled ticket
        error = self.get_modulo_and_form()
        if error and not api:
            return error

        self.context_data = {
            "categoria": self.category,
            "category_conditions": self.clausole_categoria,
            "compiled_by": self.compiled_by_user,
            "form": self.form,
            "struttura": self.struttura,
            "sub_title": "{} - {}".format(self.struttura, self.sub_title),
            "title": self.title,
        }
        if api:
            return self.context_data
        else:
            return render(request, self.template, base_context(self.context_data))

    def post(self, request, structure_slug, category_slug, api=False):
        self.get_assets(structure_slug, category_slug)
        deny_response = self.deny_response()
        if deny_response:
            return deny_response

        error = self.get_modulo_and_form()
        if error and not api:
            return error
        self.context_data = {
            "categoria": self.category,
            "category_conditions": self.clausole_categoria,
            "compiled_by": self.compiled_by_user,
            "form": self.form,
            "struttura": self.struttura,
            "sub_title": "{} - {}".format(self.struttura, self.sub_title),
            "title": self.title,
        }

        self.form = self.modulo.get_form(
            data=request.POST or getattr(request, "api_data", {}), # csrf except workaround for API integration
            files=request.FILES,
            show_conditions=True,
            current_user=request.user,
        )
        self.context_data["form"] = self.form
        if self.form.is_valid():
            # get form data in json
            form_data = deepcopy(self.form.data)

            # add static static fields to fields to pop
            # these fields are useful only in frontend
            fields_to_pop = [
                TICKET_CONDITIONS_FIELD_ID,
                TICKET_CAPTCHA_ID,
                TICKET_CAPTCHA_HIDDEN_ID,
                'csrfmiddlewaretoken'
            ]

            # if user generates an encrypted token in URL
            # no ticket is saved. compiled form is serialized
            if self.form.data.get(TICKET_GENERATE_URL_BUTTON_NAME):

                # log action
                logger.info(
                    f'[{timezone.localtime()}] user {request.user} '
                    f"generated a new ticket URL '{self.category}' "
                    "for submission"
                )

                # add the "generate url" button to fields to pop
                fields_to_pop.append(TICKET_GENERATE_URL_BUTTON_NAME)

                for i in fields_to_pop:
                    if i in form_data:
                        form_data.pop(i)

                # insert input module pk to json data
                form_data.update({TICKET_INPUT_MODULE_NAME: self.modulo.pk})

                if self.form.data.get(TICKET_COMPILED_BY_USER_NAME):
                    form_data.update(
                        {TICKET_COMPILED_BY_USER_NAME: request.user.pk}
                    )
                    form_data.update(
                        {
                            TICKET_COMPILED_CREATION_DATE: timezone.localtime().isoformat()
                        }
                    )

                # build encrypted url param with form data
                form_data = querydict_to_dict(form_data)
                encrypted_data = encrypt_to_jwe(json.dumps(form_data).encode())
                base_url = request.build_absolute_uri(
                    reverse(
                        "uni_ticket:add_new_ticket",
                        kwargs={
                            "structure_slug": self.struttura.slug,
                            "category_slug": self.category.slug,
                        },
                    )
                )
                # build url to display in message
                one_time = 1 if self.form.data.get(TICKET_COMPILED_ONE_TIME_FLAG) else 0
                compiled_ticket = CompiledTicket.objects.create(url_path=uuid_code(),
                                                                content=encrypted_data,
                                                                one_time=one_time)
                # url = base_url + "?import=" + encrypted_data
                url = f"{base_url}?import={compiled_ticket.url_path}"
                messages.add_message(
                    request,
                    messages.SUCCESS,
                    # TODO - please no ... html in localized messages ...
                    _(
                        "<b>Di seguito l'URL della richiesta precompilata</b>"
                        "<input type='text' value='{url}' id='encrypted_ticket_url' />"
                        "<button class='btn btn-sm btn-primary px-4 mt-3' onclick='copyToClipboard()'>"
                        "Copia negli appunti"
                        "</button>"
                        "<p class='text-success mt-3 mb-0' id='clipboard_message'></p>"
                        ""
                    ).format(url=url),
                )
                self.context_data["url_to_import"] = True
            #
            # if user creates the ticket
            #
            elif self.form.data.get(TICKET_CREATE_BUTTON_NAME):

                # if user is not allowed (category allowed users list)
                if (
                    self.category.allowed_users.exists()
                    and self.category.allowed_users.filter(pk=self.request.user.pk).exists()
                ):
                    return custom_message(
                        request,
                        _(
                            "Solo gli utenti abilitati "
                            "possono generare richieste "
                            "di questo tipo"
                        ),
                        status=404,
                    )

                # extends fields_to_pop list
                fields_to_pop.extend(
                    [
                        TICKET_SUBJECT_ID,
                        TICKET_DESCRIPTION_ID,
                        TICKET_CREATE_BUTTON_NAME,
                        TICKET_COMPILED_BY_USER_NAME,
                        TICKET_COMPILED_CREATION_DATE,
                    ]
                )

                for i in fields_to_pop:
                    if i in form_data:
                        form_data.pop(i)

                form_data = querydict_to_dict(form_data)

                # make a UUID based on the host ID and current time
                code = uuid_code()

                # get ticket subject and description
                subject = self.form.cleaned_data[TICKET_SUBJECT_ID]
                description = self.form.cleaned_data[TICKET_DESCRIPTION_ID]

                # destination office
                office = self.category.organizational_office

                # take a random operator (or manager)
                # only if category is_notification or user is anonymous
                random_office_operator = None
                if self.category.is_notification or not request.user.is_authenticated:
                    # get random operator from the office
                    random_office_operator = OrganizationalStructureOfficeEmployee.get_default_operator_or_manager(
                        office
                    )

                # set users for current operations and for log
                # if current_user isn't authenticated, for logging we use 'anonymous'
                self.current_user = (
                    self.request.user
                    if request.user.is_authenticated
                    else random_office_operator
                )
                self.log_user = (
                    self.request.user.username
                    if request.user.is_authenticated
                    else "anonymous"
                )

                # create ticket
                self.ticket = Ticket(
                    code=code,
                    subject=subject,
                    description=description,
                    modulo_compilato=json.dumps(form_data),
                    created_by=self.current_user,
                    input_module=self.modulo
                )

                # if ticket has been compiled by another user
                if self.compiled_by_user:
                    self.ticket.compiled_by = self.compiled_by_user
                    self.ticket.compiled = self.compiled_date

                # save ticket
                self.ticket.save()

                # compress content (default makes a check on length)
                self.ticket.compress_modulo_compilato()

                # log action
                logger.info(
                    "[{}] user {} created new ticket {}"
                    " in category {}".format(
                        timezone.localtime(),
                        self.log_user,
                        self.ticket,
                        self.category
                    )
                )

                # save ticket attachments in ticket folder
                json_stored = get_as_dict(compiled_module_json=form_data)
                _save_new_ticket_attachments(
                    ticket=self.ticket,
                    json_stored=json_stored,
                    form=self.form,
                    request_files=request.FILES,
                )

                # assign ticket to the office
                self.ticket_assignment = TicketAssignment(
                    ticket=self.ticket,
                    office=office
                )
                self.ticket_assignment.save()

                # log action
                logger.info(
                    "[{}] ticket {} assigned to "
                    "{} office".format(
                        timezone.localtime(),
                        self.ticket,
                        office
                    )
                )

                # if it's a notification ticket, take and close the ticket
                if self.category.is_notification:
                    _close_notification_ticket(
                        ticket=self.ticket,
                        user=self.current_user
                    )
                    # operator=random_office_operator,
                    # ticket_assignment=ticket_assignment)

                else:
                    # category default tasks assigned to ticket (if present)
                    _assign_default_tasks_to_new_ticket(
                        ticket=self.ticket,
                        category=self.category,
                        log_user=self.log_user
                    )

                # send success message to user
                ticket_message = (
                    self.ticket.input_module.ticket_category.confirm_message_text or
                    NEW_TICKET_CREATED_ALERT
                )

                compiled_message = ticket_message.format(self.ticket.subject)

                # Protocol
                if self.category.protocol_required:
                    self.protocolla_ticket()
                # end Protocol

                messages.add_message(request, messages.SUCCESS, compiled_message)

                # if office operators must receive notification email
                if self.category.receive_email:
                    # Send mail to ticket
                    structure = self.category.organizational_structure
                    mail_params = {
                        "hostname": settings.HOSTNAME,
                        "ticket_url": request.build_absolute_uri(
                            reverse(
                                "uni_ticket:manage_ticket_url_detail",
                                kwargs={
                                    "ticket_id": self.ticket.code,
                                    "structure_slug": structure.slug,
                                },
                            )
                        ),
                        "ticket_subject": self.ticket.subject,
                        "ticket_description": self.ticket.description,
                        "ticket_user": self.ticket.created_by,
                        "destination_office": self.category.organizational_office,
                    }
                    send_ticket_mail_to_operators(
                        request=request,
                        ticket=self.ticket,
                        category=self.category,
                        message_template=NEW_TICKET_CREATED_EMPLOYEE_BODY,
                        mail_params=mail_params,
                    )

                # if user is authenticated send mail and redirect to ticket page
                if request.user.is_authenticated:
                    # Send mail to ticket owner
                    mail_params = {
                        "hostname": settings.HOSTNAME,
                        "user": self.request.user,
                        "ticket": self.ticket.code,
                        "ticket_subject": subject,
                        "url": request.build_absolute_uri(
                            reverse(
                                "uni_ticket:ticket_detail",
                                kwargs={"ticket_id": self.ticket.code},
                            )
                        ),
                        "added_text": compiled_message,
                    }

                    m_subject = _("{} - richiesta {} creata con successo").format(
                        settings.HOSTNAME, self.ticket
                    )

                    send_custom_mail(
                        subject=m_subject,
                        recipients=self.ticket.get_owners(),
                        body=NEW_TICKET_CREATED,
                        params=mail_params,
                    )
                    # END Send mail to ticket owner

                    return redirect(
                        "uni_ticket:ticket_detail", ticket_id=self.ticket.code
                    )
                else:
                    return redirect(
                        "uni_ticket:add_new_ticket",
                        structure_slug=structure_slug,
                        category_slug=category_slug,
                    )
        else:  # pragma: no cover
            for k, v in get_labeled_errors(self.form).items():
                messages.add_message(
                    request, messages.ERROR, f"<b>{k}</b>: {strip_tags(v)}"
                )

        if api:
            return self.context_data
        else:
            return render(request, self.template, base_context(self.context_data))


@login_required
def dashboard(request):
    """
    Dashboard of user, with tickets list

    :return: render
    """

    # Ci pensa datatables a popolare la tabella
    title = _("Pannello di controllo")
    sub_title = _("Gestisci le tue richieste o creane di nuove")
    template = "user/dashboard.html"
    tickets = Ticket.objects.filter(
        Q(created_by=request.user) | Q(compiled_by=request.user)
    )
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
    # closed = tickets.filter(is_closed=True).count()
    ticket_ids = not_closed.values_list('pk', flat=True).distinct()
    messages = TicketReply.get_unread_messages_count(
        ticket_ids=ticket_ids, by_operator=True)

    d = {
        "priority_levels": PRIORITY_LEVELS,
        "sub_title": sub_title,
        "ticket_aperti": opened,
        "ticket_messages": messages,
        "ticket_non_gestiti": unassigned,
        "title": title,
    }
    return render(request, template, base_context(d))


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
        messages.add_message(
            request,
            messages.ERROR,
            _("Impossibile modificare una richiesta protocollata"),
        )
        return redirect("uni_ticket:ticket_detail", ticket_id=ticket.code)

    # deny action if user is not the owner but has compiled only
    if not request.user == ticket.created_by:
        messages.add_message(
            request,
            messages.ERROR,
            TICKET_SHARING_USER_ERROR_MESSAGE.format(ticket.created_by),
        )
        return redirect("uni_ticket:ticket_detail", ticket_id=ticket.code)

    categoria = ticket.input_module.ticket_category
    title = _("Modifica ticket")
    sub_title = ticket
    allegati = ticket.get_allegati_dict()
    path_allegati = get_path(ticket.get_folder())
    form = ticket.compiled_form(files=None, remove_filefields=allegati)
    form_allegati = ticket.compiled_form(
        files=None, remove_filefields=False, remove_datafields=True
    )
    template = "user/ticket_edit.html"
    d = {
        "allegati": allegati,
        "categoria": categoria,
        "form": form,
        "form_allegati": form_allegati,
        "path_allegati": path_allegati,
        "sub_title": sub_title,
        "ticket": ticket,
        "title": title,
    }
    if request.method == "POST":
        fields_to_pop = [TICKET_CONDITIONS_FIELD_ID,
                         'csrfmiddlewaretoken']
        # get form data in json
        json_response = deepcopy(request.POST)
        for i in fields_to_pop:
            if i in json_response:
                json_response.pop(i)
        json_response = querydict_to_dict(json_response)
        # Costruisco il form con il json dei dati inviati e tutti gli allegati
        # json_response[settings.ATTACHMENTS_DICT_PREFIX]=allegati
        # rimuovo solo gli allegati che sono stati già inseriti
        modulo = ticket.get_form_module()
        form = modulo.get_form(
            data=json_response, files=request.FILES, remove_filefields=allegati
        )

        d["form"] = form

        if form.is_valid():
            if request.FILES:
                json_response[settings.ATTACHMENTS_DICT_PREFIX] = allegati
                json_stored = get_as_dict(compiled_module_json=json_response)
                _save_new_ticket_attachments(
                    ticket=ticket,
                    json_stored=json_stored,
                    form=form,
                    request_files=request.FILES,
                )
            elif allegati:
                # If data aren't updated (the same as the original)
                json_response[settings.ATTACHMENTS_DICT_PREFIX] = allegati

            # save module
            ticket.save_data(
                form.cleaned_data[TICKET_SUBJECT_ID],
                form.cleaned_data[TICKET_DESCRIPTION_ID],
                json_response,
            )

            # compress content (default makes a check on length)
            ticket.compress_modulo_compilato()

            # update modified date
            ticket.update_log(user=request.user, note=_("Ticket modificato"))

            # log action
            logger.info(
                "[{}] user {} edited ticket {}".format(
                    timezone.localtime(), request.user, ticket
                )
            )

            # Attach a message to redirect action
            messages.add_message(
                request, messages.SUCCESS, _(
                    "Modifica effettuata con successo")
            )
            return redirect("uni_ticket:ticket_edit", ticket_id=ticket_id)
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )

    return render(request, template, base_context(d))


@login_required
@require_POST
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
    logger.info(
        "[{}] user {} deleted file {}".format(
            timezone.localtime(), request.user.username, path_allegato
        )
    )

    set_as_dict(ticket, ticket_details)
    ticket.update_log(user=request.user, note=_("Elimina allegato"))

    # log action
    logger.info(
        "[{}] user {} deleted attachment "
        "{} for ticket {}".format(
            timezone.localtime(), request.user.username, nome_file, ticket
        )
    )

    messages.add_message(
        request, messages.SUCCESS, _("Allegato eliminato correttamente")
    )
    return redirect("uni_ticket:ticket_edit", ticket_id=ticket_id)


@login_required
@require_POST
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
        messages.add_message(
            request,
            messages.ERROR,
            _("Impossibile eliminare una richiesta protocollata"),
        )
        return redirect("uni_ticket:ticket_detail", ticket_id=ticket.code)

    # deny action if user is not the owner but has compiled only
    if not request.user == ticket.created_by:
        messages.add_message(
            request,
            messages.ERROR,
            TICKET_SHARING_USER_ERROR_MESSAGE.format(
                ticket.created_by),
        )
        return redirect("uni_ticket:ticket_detail", ticket_id=ticket.code)

    ticket_assignment = TicketAssignment.objects.filter(ticket=ticket).first()

    # log action
    logger.info(
        "[{}] ticket {} assignment"
        " to office {}"
        " has been deleted"
        " by user {}".format(
            timezone.localtime(), ticket, ticket_assignment.office, request.user
        )
    )

    ticket_assignment.delete()

    # Send mail to ticket owner
    mail_params = {
        "hostname": settings.HOSTNAME,
        "user": request.user,
        "status": _("eliminato"),
        "ticket": ticket,
    }
    m_subject = _("{} - richiesta {} eliminata").format(settings.HOSTNAME, ticket)

    send_custom_mail(
        subject=m_subject,
        recipients=ticket.get_owners(),
        body=TICKET_DELETED,
        params=mail_params,
    )
    # END Send mail to ticket owner

    # log action
    logger.info(
        "[{}] user {} deleted ticket {}".format(
            timezone.localtime(), request.user, ticket
        )
    )

    messages.add_message(
        request,
        messages.SUCCESS,
        _("Ticket {} eliminato correttamente").format(ticket.code),
    )

    ticket.delete()

    return redirect("uni_ticket:user_unassigned_ticket")


# @login_required
# @is_the_owner
# decorators in urls.py (print view call this view but with different decorators)
class TicketDetail(View):
    """
    Shows ticket details

    :type ticket_id: String
    :type template: String

    :param ticket_id: ticket code
    :param attachment: template to user (can change if specified)

    :return: render
    """
    def get(self, request, ticket_id:str, api:bool=False, printable:bool=False, template="user/ticket_detail.html"):

        ticket = get_object_or_404(Ticket.objects.select_related('created_by','compiled_by','input_module__ticket_category'),
                                   code=ticket_id)
        modulo_compilato = ticket.get_modulo_compilato()
        ticket_details = get_as_dict(
            compiled_module_json=modulo_compilato, allegati=False, formset_management=False
        )
        allegati = ticket.get_allegati_dict()
        path_allegati = get_path(ticket.get_folder())
        ticket_form = ticket.input_module.get_form(
            files=allegati, remove_filefields=False)
        priority = ticket.get_priority()

        ticket_logs = Log.objects.filter(
            content_type_id=ContentType.objects.get_for_model(ticket).pk,
            object_id=ticket.pk,
            is_public=True
        ).select_related('user', 'app_io_message')
        ticket_messages = TicketReply.get_unread_messages_count(
            ticket_ids=[ticket.pk], by_operator=True)
        ticket_task = Task.objects.filter(ticket=ticket)
        if printable:
            ticket_task = ticket_task.filter(is_printable=True)
        ticket_dependences = ticket.get_dependences()
        title = ticket.subject
        sub_title = ticket.code
        ticket_assignments = TicketAssignment.objects.filter(ticket=ticket)\
                                                     .select_related('office','assigned_by','taken_by')

        category_conditions = ticket.input_module.ticket_category.get_conditions(
            is_printable=True
        )

        self.data = {
            "title": title,
            "allegati": allegati,
            "category_conditions": category_conditions,
            "dependences": ticket_dependences,
            "details": ticket_details,
            "path_allegati": path_allegati,
            "priority": priority,
            "sub_title": sub_title,
            "ticket": ticket,
            "ticket_assignments": ticket_assignments,
            "ticket_form": ticket_form,
            "ticket_messages": ticket_messages,
            "logs": ticket_logs,
            "ticket_task": ticket_task,
        }
        if api:
            return self.data
        else:
            return render(request, template, base_context(self.data))


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

    agent_replies = ticket_replies.filter(read_by=None).exclude(structure=None)
    if request.user == ticket.created_by:
        for reply in agent_replies:
            reply.read_by = request.user
            reply.read_date = timezone.localtime()
            reply.save(update_fields=["read_by", "read_date"])

    if request.method == "POST":

        if not ticket.is_open():
            # log action
            logger.info(
                "[{}] user {} tried to submit"
                " a message for the not opened ticket {}".format(
                    timezone.localtime(), request.user, ticket
                )
            )
            return custom_message(request, _("La richiesta non è modificabile"))

        form = ReplyForm(request.POST, request.FILES)
        if form.is_valid():
            ticket_reply = form.save(commit=False)
            ticket_reply.ticket = ticket
            ticket_reply.owner = request.user
            ticket_reply.save()

            # log action
            logger.info(
                "[{}] user {} submitted a message"
                " for ticket {}".format(
                    timezone.localtime(),
                    request.user,
                    ticket)
            )

            # add to ticket log history
            log_msg = _("Nuovo messaggio (da utente). Oggetto:{}").format(
                ticket_reply.subject
            )
            ticket.update_log(user=request.user, note=log_msg, send_mail=False)

            # Send mail to ticket owner
            mail_params = {
                "hostname": settings.HOSTNAME,
                "status": _("inviato"),
                "ticket": ticket,
                "user": request.user,
                "url": request.build_absolute_uri(
                    reverse(
                        "uni_ticket:ticket_message",
                        kwargs={"ticket_id": ticket.code}
                    )
                ),
            }
            m_subject = _("{} - richiesta {} messaggio inviato").format(
                    settings.HOSTNAME,
                    ticket
                )

            send_custom_mail(
                subject=m_subject,
                recipients=[request.user],
                body=USER_TICKET_MESSAGE,
                params=mail_params,
            )
            # END Send mail to ticket owner

            # Send email to operators (if category flag is checked)
            category = ticket.input_module.ticket_category
            return_url = request.build_absolute_uri(
                reverse(
                    "uni_ticket:manage_ticket_message_url",
                    kwargs={
                        "ticket_id": ticket.code,
                        "structure_slug": category.organizational_structure.slug,
                    },
                )
            )
            if category.receive_email:
                # Send mail to ticket
                mail_params = {
                    "hostname": settings.HOSTNAME,
                    "url": return_url,
                    "ticket": ticket,
                }
                send_ticket_mail_to_operators(
                    request=request,
                    ticket=ticket,
                    category=category,
                    message_template=NEW_MESSAGE_RECEIVED_EMPLOYEE_BODY,
                    mail_params=mail_params,
                )
            # END Send email to operators

            messages.add_message(
                request, messages.SUCCESS, _("Messaggio inviato con successo")
            )
            return redirect("uni_ticket:ticket_message", ticket_id=ticket_id)
        else:  # pragma: no cover
            for k, v in get_labeled_errors(form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )
    d = {
        "form": form,
        "sub_title": ticket.__str__(),
        "sub_title_2": ticket.description,
        "ticket": ticket,
        "ticket_replies": ticket_replies,
        "title": title,
    }
    template = "user/ticket_assistance.html"
    return render(request, template, base_context(d))


@method_decorator(login_required, name="dispatch")
@method_decorator(is_the_owner, name="dispatch")
class TaskDetail(View):  # pragma: no cover
    """
    Task details page

    :param ticket_id: String
    :param task_id: String

    :type ticket_id: ticket code
    :type task_id: task code

    :return: render
    """

    def get(self, request, ticket_id:str, task_id:str):
        ticket = get_object_or_404(Ticket, code=ticket_id)
        task = get_object_or_404(Task, code=task_id, ticket=ticket)
        if not task.is_public:
            return custom_message(request, _("Attività riservata agli operatori"))

        priority = task.get_priority()
        title = _("Dettaglio task")
        d = {"priority": priority, "sub_title": task, "task": task, "title": title}
        template = "user/task_detail.html"
        return render(request, template, base_context(d))


@method_decorator(login_required, 'dispatch')
@method_decorator(is_the_owner, 'dispatch')
class TicketClose(View):
    template = "user/ticket_close.html"

    def dispatch(self, request, ticket_id:str, *args, **kwargs) -> Union[HttpResponse, HttpResponseRedirect]:
        self.ticket = get_object_or_404(Ticket, code=ticket_id)
        self.title = _("Chiusura della richiesta")
        self.sub_title = self.ticket
        self.context_data = {
            "sub_title": self.sub_title,
            "ticket": self.ticket,
            "title": self.title,
        }
        if self.ticket.is_closed:
            # log action
            logger.info(
                "[{}] user {} tried to close "
                " the already closed ticket {}".format(
                    timezone.localtime(), request.user, self.ticket
                )
            )

            return custom_message(request, _("La richiesta è già chiusa!"))

        # deny action if user is not the owner but has compiled only
        if not request.user == self.ticket.created_by:
            messages.add_message(
                request,
                messages.ERROR,
                TICKET_SHARING_USER_ERROR_MESSAGE.format(
                    self.ticket.created_by),
            )
            return redirect(
                "uni_ticket:ticket_detail", ticket_id=self.ticket.code
            )
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, api:bool = False):
        """
        Ticket closing by owner user

        :param ticket_id: String

        :type ticket_id: ticket code

        :return: render
        """
        self.form = BaseTicketCloseForm()
        self.context_data['form'] = self.form
        if api:
            return self.contenxt_data
        else:
            return render(request, self.template, base_context(self.context_data))

    def post(self, request, api:bool = False):
        self.form = BaseTicketCloseForm(request.POST or getattr(request, "api_data")) # API csrf token workaround
        self.context_data['form'] = self.form
        if self.form.is_valid():
            motivazione = self.form.cleaned_data["note"]
            self.ticket.close(user= request.user, motivazione=motivazione)
            self.ticket.update_log(
                user=request.user,
                note=_("Chiusura richiesta da utente proprietario: {}").format(
                    motivazione
                ),
            )
            messages.add_message(
                request,
                messages.SUCCESS,
                _("Richiesta {} chiusa correttamente").format(self.ticket),
            )

            # log action
            logger.info(
                f"[{timezone.localtime()}] user {request.user} "
                f"closed ticket {self.ticket}"
            )

            return redirect("uni_ticket:ticket_detail", self.ticket.code)
        else:  # pragma: no cover
            for k, v in get_labeled_errors(self.form).items():
                messages.add_message(
                    request, messages.ERROR, "<b>{}</b>: {}".format(
                        k, strip_tags(v))
                )


@login_required
@require_POST
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
        logger.info(
            "[{}] {} tried to reopen not closed ticket {} "
            "".format(timezone.localtime(), request.user, ticket)
        )
        return custom_message(request, _("La richiesta non è stata chiusa"))

    if ticket.closed_by:
        logger.info(
            "[{}] {} tried to reopen ticket {} "
            " closed by operator".format(
                timezone.localtime(), request.user, ticket)
        )
        return custom_message(
            request,
            _(
                "La richiesta è stata chiusa "
                "da un operatore e non può "
                "essere riaperta"
            ),
        )

    if ticket.is_notification:
        logger.info(
            "[{}] {} tried to reopen notification ticket {} "
            "".format(timezone.localtime(), request.user, ticket)
        )
        return custom_message(
            request,
            _("La richiesta è di tipo " "notifica e non può essere " "riaperta"),
        )

    # check if user has already open a ticket of this category
    category = ticket.input_module.ticket_category
    if not category.user_multiple_open_tickets and Ticket.existent_open_ticket(
        request.user, category
    ):
        return custom_message(
            request,
            _(
                "Esistono già tue richieste aperte"
                " di questa tipologia."
                " Non puoi riaprire questa"
                " fino a quando le altre non verranno chiuse"
            ),
        )

    ticket.is_closed = False
    ticket.save(update_fields=["is_closed"])

    msg = _("Riapertura richiesta {} da utente proprietario").format(ticket)
    # log action
    logger.info(
        "[{}] {} reopened ticket {}".format(
            timezone.localtime(), request.user, ticket)
    )

    ticket.update_log(user=request.user, note=msg)
    messages.add_message(
        request,
        messages.SUCCESS,
        _("Richiesta {} riaperta correttamente").format(ticket),
    )
    return redirect("uni_ticket:ticket_detail", ticket_id=ticket_id)


@login_required
def chat_new_preload(request, structure_slug=None):  # pragma: no cover
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
        struttura = get_object_or_404(
            OrganizationalStructure, slug=structure_slug, is_active=True
        )
        sub_title = struttura
    d = {
        "structure_slug": structure_slug,
        "strutture": strutture,
        "sub_title": sub_title,
        "title": title,
    }
    return render(request, template, base_context(d))


@login_required
def ticket_clone(request, ticket_id):
    main_ticket = get_object_or_404(
        Ticket, Q(created_by=request.user) | Q(compiled_by=request.user), code=ticket_id
    )
    # if ticket is not closed and owner has closed it
    # if not main_ticket.is_closed:
    # return custom_message(request, _("Operazione non permessa. "
    # "La richiesta è ancora attiva"))

    # if ticket module is out of date
    if not main_ticket.input_module.is_active:
        return custom_message(
            request, _(
                "Il modulo che stai cercando " "di usare non è più attivo.")
        )

    category = main_ticket.input_module.ticket_category
    form_data = main_ticket.get_modulo_compilato()

    form_data.update({TICKET_INPUT_MODULE_NAME: main_ticket.input_module.pk})
    form_data.update({TICKET_SUBJECT_ID: main_ticket.subject})
    form_data.update({TICKET_DESCRIPTION_ID: main_ticket.description})

    # build encrypted url param with form data
    encrypted_data = encrypt_to_jwe(json.dumps(form_data).encode())
    compiled_ticket = CompiledTicket.objects.create(url_path=uuid_code(),
                                                    content=encrypted_data)
                                                    # one_time=True)
    base_url = reverse(
        "uni_ticket:add_new_ticket",
        kwargs={
            "structure_slug": category.organizational_structure.slug,
            "category_slug": category.slug,
        },
    )
    return HttpResponseRedirect(f"{base_url}?import={compiled_ticket.url_path}")


@login_required
@has_access_to_ticket
def ticket_detail_print(request, ticket_id, ticket):  # pragma: no cover
    """
    Displays ticket print version

    :type ticket_id: String
    :type ticket: Ticket (from @has_access_to_ticket)

    :param ticket_id: ticket code
    :param ticket: ticket object (from @has_access_to_ticket)

    :return: view response
    """
    response = TicketDetail().get(request=request,
                                  ticket_id=ticket_id,
                                  template="ticket_detail_print.html",
                                  printable=True)
    return response


@login_required
@has_access_to_ticket
def download_ticket_pdf(request,
                        ticket_id,
                        ticket,
                        template="ticket_detail_print_pdf.html"):  # pragma: no cover
    response = TicketDetail().get(request=request,
                                  ticket_id=ticket_id,
                                  template=template,
                                  printable=True)

    # file names
    pdf_fname = "{}.pdf".format(ticket.code)

    # get PDF

    # no need to merge if not attachments to manage :)
    return response_as_pdf(response, pdf_fname)
