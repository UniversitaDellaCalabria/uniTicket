from django.conf import settings
from django.utils.translation import gettext_lazy as _


# for javascript datepickers
JS_DEFAULT_DATETIME_FORMAT = getattr(
    settings, "JS_DEFAULT_DATETIME_FORMAT", "DD/MM/YYYY HH:mm"
)

# system attachments folders
TICKET_ATTACHMENT_FOLDER = getattr(
    settings, "TICKET_ATTACHMENT_FOLDER", "ticket")
TICKET_CATEGORIES_FOLDER = getattr(
    settings, "TICKET_CATEGORIES_FOLDER", "categories")
TICKET_MESSAGES_ATTACHMENT_SUBFOLDER = getattr(
    settings, "TICKET_MESSAGES_ATTACHMENT_SUBFOLDER", "messages"
)
TICKET_TASK_ATTACHMENT_SUBFOLDER = getattr(
    settings, "TICKET_TASK_ATTACHMENT_SUBFOLDER", "task"
)
CATEGORY_CONDITIONS_ATTACHMENT_SUBFOLDER = getattr(
    settings, "CATEGORY_CONDITIONS_ATTACHMENT_SUBFOLDER", "conditions"
)

UNITICKET_JWE_RSA_KEY_PATH = getattr(
    settings, "UNITICKET_JWE_RSA_KEY_PATH", "saml2_sp/saml2_config/certificates/key.pem"
)
UNITICKET_JWE_ALG = getattr(settings, "UNITICKET_JWE_ALG", "RSA-OAEP")
UNITICKET_JWE_ENC = getattr(settings, "UNITICKET_JWE_ENC", "A128CBC-HS256")

# superusers view all
SUPER_USER_VIEW_ALL = getattr(settings, "SUPER_USER_VIEW_ALL", True)

# show ticket priority to simple userse
SIMPLE_USER_SHOW_PRIORITY = getattr(
    settings, "SIMPLE_USER_SHOW_PRIORITY", False)

# category conditions form field
TICKET_CONDITIONS_FIELD_ID = getattr(
    settings, "TICKET_CONDITIONS_FIELD_ID", "condizioni_field_id"
)
TICKET_CONDITIONS_TEXT = getattr(
    settings,
    "TICKET_CONDITIONS_TEXT",
    _(
        "Dichiara di aver letto "
        "e compreso quanto scritto sopra "
        "e di assumersi ogni responsabilità "
        "su quanto di seguito dichiarato"
    ),
)

# new ticket heading text (user informations)
SHOW_HEADING_TEXT = getattr(settings, "SHOW_HEADING_TEXT", True)
TICKET_HEADING_TEXT = getattr(
    settings,
    "TICKET_HEADING_TEXT",
    _(
        "Soggetto richiedente: <b>{user}</b>"
        '<br><span class="x-small">[{taxpayer}]</span>'
    ),
)

TICKET_COMPILED_HEADING_TEXT = getattr(
    settings,
    "TICKET_COMPILED_HEADING_TEXT",
    _("Compilato da: <b>{user}</b>" '<br><span class="x-small">[{taxpayer}]</span>'),
)

# form fields names
# ticket subject
TICKET_SUBJECT_ID = getattr(settings, "TICKET_SUBJECT_ID", "ticket_subject")

TICKET_SUBJECT_LABEL = getattr(
    settings, "TICKET_SUBJECT_LABEL", _("Oggetto della Richiesta")
)
TICKET_SUBJECT_HELP_TEXT = getattr(
    settings,
    "TICKET_SUBJECT_HELP_TEXT",
    _(
        "Il campo Oggetto è impostato con "
        "la denominazione della richiesta. "
        "E' possibile modificarlo o integrarlo "
        "per fornire indicazioni specifiche"
    ),
)

# ticket description
TICKET_DESCRIPTION_ID = getattr(
    settings, "TICKET_DESCRIPTION_ID", "ticket_description")
TICKET_DESCRIPTION_LABEL = getattr(
    settings, "TICKET_DESCRIPTION_LABEL", _("Descrizione")
)
TICKET_DESCRIPTION_HELP_TEXT = getattr(
    settings,
    "TICKET_DESCRIPTION_HELP_TEXT",
    _(
        "Il campo Descrizione è impostato con "
        "la descrizione generica della richiesta. "
        "E' possibile modificarlo o integrarlo "
        "per fornire indicazioni specifiche"
    ),
)

# captcha
TICKET_CAPTCHA_ID = getattr(
    settings, "TICKET_CAPTCHA_ID", "ticket_captcha"
)
TICKET_CAPTCHA_HIDDEN_ID = getattr(
    settings, "TICKET_CAPTCHA_HIDDEN_ID", "ticket_captcha_hidden"
)
TICKET_CAPTCHA_LABEL = getattr(
    settings, "TICKET_CAPTCHA_LABEL", _("Codice di verifica")
)

# new ticket submit buttons (create / generate import URL)
TICKET_CREATE_BUTTON_NAME = getattr(
    settings, "TICKET_CREATE_BUTTON_NAME", "confirm_submit"
)
TICKET_GENERATE_URL_BUTTON_NAME = getattr(
    settings, "TICKET_GENERATE_URL_BUTTON_NAME", "generate_url_submit"
)
TICKET_COMPILED_BY_USER_NAME = getattr(
    settings, "TICKET_COMPILED_BY_USER_NAME", "compiled_by_user"
)
TICKET_COMPILED_CREATION_DATE = getattr(
    settings, "TICKET_COMPILED_CREATION_DATE", "compiled_date"
)
TICKET_INPUT_MODULE_NAME = getattr(
    settings, "TICKET_INPUT_MODULE_NAME", "ticket_input_module"
)

# priority levels
PRIORITY_LEVELS = getattr(
    settings,
    "PRIORITY_LEVELS",
    (
        (-2, _("Molto alta")),
        (-1, _("Alta")),
        (0, _("Normale")),
        (1, _("Bassa")),
        (2, _("Molto bassa")),
    ),
)

# closing levels
CLOSING_LEVELS = getattr(
    settings,
    "CLOSING_LEVELS",
    (
        (-1, _("Rifiutata")),
        (0, _("Non risolta")),
        (1, _("Risolta con successo")),
        (2, _("Non definita")),
    ),
)

# If 0 = Unlimited
MAX_DAILY_TICKET_PER_USER = getattr(settings, "MAX_DAILY_TICKET_PER_USER", 10)

# user contexts
CONTEXT_SIMPLE_USER = getattr(settings, "CONTEXT_SIMPLE_USER", _("Utente"))

# To change the URLs prefix for every user type
MANAGER_PREFIX = getattr(settings, "MANAGER_PREFIX", "Manager")
OPERATOR_PREFIX = getattr(settings, "OPERATOR_PREFIX", "Operatore")
USER_PREFIX = getattr(settings, "USER_PREFIX", "user")

# Do not edit! - START
MANAGEMENT_URL_PREFIX = {
    "manager": MANAGER_PREFIX,
    "operator": OPERATOR_PREFIX,
    "user": USER_PREFIX,
}
# Do not edit! - END

# ticket competence abandoned
NO_MORE_COMPETENCE_OVER_TICKET = getattr(
    settings, "NO_MORE_COMPETENCE_OVER_TICKET", _(
        "Nessuna competenza sulla richiesta")
)
# ticket readonly access
READONLY_COMPETENCE_OVER_TICKET = getattr(
    settings,
    "READONLY_COMPETENCE_OVER_TICKET",
    _("Hai accesso alla richiesta in sola lettura"),
)

# min ticket content length (digits) to compress
TICKET_MIN_DIGITS_TO_COMPRESS = getattr(
    settings, "TICKET_MIN_DIGITS_TO_COMPRESS", 90)

# Access level to categories
# Override for your own context

# This parameters define the roles of users to open ticket
# If True, an employee is a user that has this parameter filled (in user model)
# If False, an employee is a user that is mapped as OrganizationalStructureOfficeEmployee
EMPLOYEE_ATTRIBUTE_NAME = getattr(
    settings, "EMPLOYEE_ATTRIBUTE_NAME", "identificativo_dipendente"
)
EMPLOYEE_ATTRIBUTE_LABEL = getattr(
    settings, "EMPLOYEE_ATTRIBUTE_LABEL", "Matricola Dipendente"
)

# Label
ORGANIZATION_EMPLOYEE_LABEL = getattr(
    settings, "ORGANIZATION_EMPLOYEE_LABEL", "Dipendenti"
)
# If True, an internal user (not guest) is a user that has this filled (in user model)
# If False, an internal user is a user that is mapped as OrganizationalStructureOfficeEmployee
USER_ATTRIBUTE_NAME = getattr(
    settings, "USER_ATTRIBUTE_NAME", "identificativo_utente")
USER_ATTRIBUTE_LABEL = getattr(
    settings, "USER_ATTRIBUTE_LABEL", "Matricola utente")

# Ticket categories CSV export
# additional user fields to export
ADDITIONAL_USER_FIELDS = getattr(
    settings, "ADDITIONAL_USER_FIELDS", [
        EMPLOYEE_ATTRIBUTE_NAME,
        USER_ATTRIBUTE_NAME]
)

# Label
ORGANIZATION_USER_LABEL = getattr(
    settings, "ORGANIZATION_USER_LABEL", "Studenti")

# error message for user that has compiled a request but it's not the owner
TICKET_SHARING_USER_ERROR_MESSAGE = getattr(
    settings,
    "TICKET_SHARING_USER_ERROR_MESSAGE",
    _(
        "Impossibile effettuare l'operazione."
        "<br>"
        "Nonostante tu abbia precompilato la richiesta, "
        "è l'utente <b>{}</b> che l'ha sottomessa"
    ),
)

# E-mail messages
MSG_HEADER = getattr(
    settings,
    "MSG_HEADER",
    _(
        """Gentile utente,
questo messaggio è stato inviato da {hostname}.
Per favore non rispondere a questa email.

-------------------

"""
    ),
)

MSG_FOOTER = getattr(
    settings,
    "MSG_FOOTER",
    _(
        """

-------------------

Per problemi tecnici contatta il nostro staff.
Cordiali saluti.
"""
    ),
)

UNAVAILABLE_TICKET_CATEGORY = getattr(
    settings,
    "UNAVAILABLE_TICKET_CATEGORY",
    _("""La tipologia di richiesta non è attiva"""),
)

NEW_TICKET_CREATED_ALERT = getattr(
    settings, "NEW_TICKET_CREATED_ALERT", _(
        """Richiesta "{}" creata con successo""")
)

NEW_TICKET_CREATED = getattr(
    settings,
    "NEW_TICKET_CREATED",
    _(
        """{added_text}

L'identificativo univoco di questa transazione è {ticket}.

Clicca qui {url} per prenderne visione."""
    ),
)

TICKET_UPDATED = getattr(
    settings,
    "TICKET_UPDATED",
    _(
        """La richiesta "{ticket}" è stata aggiornata con il seguente messaggio:

{message}"""
    ),
)

USER_TICKET_MESSAGE = getattr(
    settings,
    "USER_TICKET_MESSAGE",
    _(
        """Hai {status} un nuovo messaggio per la richiesta \"{ticket}\"

Oggetto: {message_subject}

Testo: {message_text}

Clicca qui {url} per aprire il pannello dei messaggi."""
    ),
)

TICKET_DELETED = getattr(
    settings,
    "TICKET_DELETED",
    _("""La richiesta "{ticket}" è stata eliminata correttamente."""),
)

SUMMARY_USER_EMAIL = getattr(
    settings,
    "SUMMARY_USER_EMAIL",
    _(
        """La seguente richiesta {event msg}:

{ticket}"""
    ),
)

SUMMARY_EMPLOYEE_EMAIL = getattr(
    settings,
    "SUMMARY_EMPLOYEE_EMAIL",
    _(
        """Ci sono {opened_ticket_number} richieste da gestire.

{tickets_per_office}"""
    ),
)

NEW_TICKET_CREATED_EMPLOYEE_BODY = getattr(
    settings,
    "NEW_TICKET_CREATED_EMPLOYEE_BODY",
    _(
        """E' stata effettuata una nuova richiesta all'ufficio {destination_office}.

Utente: {ticket_user}
Oggetto: {ticket_subject}
Descrizione: {ticket_description}

URL: {ticket_url}"""
    ),
)

NEW_MESSAGE_RECEIVED_EMPLOYEE_BODY = getattr(
    settings,
    "NEW_MESSAGE_RECEIVED_EMPLOYEE_BODY",
    _(
        """Hai ricevuto un nuovo messaggio per la richiesta \"{ticket}\"

Oggetto: {message_subject}

Testo: {message_text}

Clicca qui {url} per aprire il pannello dei messaggi."""
    ),
)

NEW_TICKET_ASSIGNED_TO_OPERATOR_BODY = getattr(
    settings,
    "NEW_TICKET_ASSIGNED_TO_OPERATOR_BODY",
    _(
        """Ti è stata assegnata una nuova richiesta da {manager}.

Utente: {ticket_user}
Oggetto: {ticket_subject}
Descrizione: {ticket_description}

URL: {ticket_url}"""
    ),
)

# Old english version
NEW_TICKET_UPDATE_OLD_EN = getattr(
    settings,
    "NEW_TICKET_UPDATE_OLD_EN",
    _(
        "Dear user,"
        "you have successfully {status} the ticket:"
        ""
        "{ticket}"
        ""
        "This message was sent to you by {hostname}."
        "Please do not reply to this email."
    ),
)

USER_TICKET_MESSAGE_OLD_EN = getattr(
    settings,
    "USER_TICKET_MESSAGE_OLD_EN",
    _(
        "Dear {user},"
        "you have successfully {status} a message for ticket:"
        ""
        "{ticket}"
        ""
        "This message was sent to you by {hostname}."
        "Please do not reply to this email."
    ),
)

TICKET_UPDATED_OLD_EN = getattr(
    settings,
    "TICKET_UPDATED_OLD_EN",
    _(
        "Dear {user},"
        "the ticket:"
        ""
        "{ticket}"
        ""
        "has been updated with the message:"
        ""
        "{message}."
        ""
        "This message was sent to you by {hostname}."
        "Please do not reply to this email."
    ),
)

SUMMARY_USER_EMAIL_OLD_EN = getattr(
    settings,
    "SUMMARY_USER_EMAIL_OLD_EN",
    _(
        "Dear {user},"
        "the following ticket {event_msg}:"
        ""
        "{ticket}"
        ""
        "This message was sent to you by {hostname}."
        "Please do not reply to this email."
    ),
)

SUMMARY_EMPLOYEE_EMAIL_OLD_EN = getattr(
    settings,
    "SUMMARY_EMPLOYEE_EMAIL_OLD_EN",
    _(
        "Dear {user},"
        "You have {open_ticket_number} tickets to manage."
        ""
        "{tickets_per_office}"
        ""
        "This message was sent to you by {hostname}."
        "Please do not reply to this email."
    ),
)

STATS_DEFAULT_DATE_START_DELTA_DAYS = getattr(
    settings, "STATS_DEFAULT_DATE_START_DELTA_DAYS", 7
)
JS_CHART_CDN_URL = getattr(
    settings, "JS_CHART_CDN_URL", "https://cdn.jsdelivr.net/npm/apexcharts"
)
STATS_TIME_SLOTS = getattr(
    settings,
    "STATS_TIME_SLOTS",
    {
        1: range(8, 14),  # 8 - 13:59
        2: range(14, 19), # 14 - 18:59
        3: range(19, 22), # 19 - 21:59
        4: range(22, 24),  # 22 - 23:59
        5: range(0, 8)    # 0 - 7:59
    }
)

STATS_MAX_DAYS = getattr(settings, "STATS_MAX_DAYS", 332)

STATS_HEAT_MAP_RANGES = getattr(settings, "STATS_HEAT_MAP_RANGES",
    [
        {
            "from": 0,
            "to": 5,
            "name": 'low',
            "color": '#00A100'
        },
        {
            "from": 6,
            "to": 20,
            "name": 'medium',
            "color": '#128FD9'
        },
        {
            "from": 21,
            "to": 50,
            "name": 'high',
            "color": '#FFB200'
        },
        {
            "from": 51,
            "to": 250,
            "name": 'extreme',
            "color": '#FF0000'
        }
    ]
)

STATS_SHOW_TICKETS_BY_USER = True

PRECOMPILED_TICKET_EXPIRE_DAYS = getattr(
    settings, 'PRECOMPILED_TICKET_EXPIRE_DAYS', 7)

