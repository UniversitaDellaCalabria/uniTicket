from django.utils.translation import gettext_lazy as _

# system attachments folders
LOGOS_FOLDER = 'logos'
STRUCTURES_FOLDER = 'structures'
TICKET_ATTACHMENT_FOLDER = 'ticket'
TICKET_CATEGORIES_FOLDER = 'categories'
TICKET_MESSAGES_ATTACHMENT_SUBFOLDER = 'messages'
TICKET_TASK_ATTACHMENT_SUBFOLDER = 'task'
CATEGORY_CONDITIONS_ATTACHMENT_SUBFOLDER = 'conditions'

# superusers view all
SUPER_USER_VIEW_ALL = True

# show ticket priority to simple userse
SIMPLE_USER_SHOW_PRIORITY = False

# category conditions form field
TICKET_CONDITIONS_FIELD_ID = 'condizioni_field_id'
TICKET_CONDITIONS_TEXT = _('Dichiara altresì di aver letto '
                           'e compreso quanto scritto sopra '
                           'e di assumere ogni responsabilità '
                           'su quanto di seguito dichiarato')

# new ticket heading text (user informations)
SHOW_HEADING_TEXT = True
TICKET_HEADING_TEXT = _('Soggetto richiedente: <b>{user}</b>'
                        '<br><span class="x-small">[{taxpayer}]</span>')

# form fields names

# ticket subject
TICKET_SUBJECT_ID = 'ticket_subject'
TICKET_SUBJECT_LABEL = _('Oggetto della Richiesta')
TICKET_SUBJECT_HELP_TEXT = _('Il campo Oggetto è impostato con '
                             'la denominazione della richiesta. '
                             'E\' possibile modificarlo o integrarlo '
                             'per fornire indicazioni specifiche')

# ticket description
TICKET_DESCRIPTION_ID = 'ticket_description'
TICKET_DESCRIPTION_LABEL = _('Descrizione')
TICKET_DESCRIPTION_HELP_TEXT = _('Il campo Descrizione è impostato con '
                                 'la descrizione generica della richiesta. '
                                 'E\' possibile modificarlo o integrarlo '
                                 'per fornire indicazioni specifiche')

# captcha
TICKET_CAPTCHA_ID = 'ticket_captcha'
TICKET_CAPTCHA_HIDDEN_ID = 'ticket_captcha_hidden'
TICKET_CAPTCHA_LABEL = _('Codice di verifica')

# new ticket submit buttons (create / generate import URL)
TICKET_CREATE_BUTTON_NAME = 'confirm_submit'
TICKET_GENERATE_URL_BUTTON_NAME  = 'generate_url_submit'
TICKET_COMPILED_BY_USER_NAME = 'compiled_by_user'
TICKET_INPUT_MODULE_NAME = 'ticket_input_module'

# priority levels
PRIORITY_LEVELS = (
                    ('-2',_('Molto alta')),
                    ('-1',_('Alta')),
                    ('0',_('Normale')),
                    ('1',_('Bassa')),
                    ('2',_('Molto bassa')),
                  )

# If 0 = Unlimited
MAX_DAILY_TICKET_PER_USER = 10

# user contexts
CONTEXT_SIMPLE_USER = _('Utente')

# To change the URLs prefix for every user type
MANAGER_PREFIX = 'Manager'
OPERATOR_PREFIX = 'Operatore'
USER_PREFIX = 'user'

# Do not edit! - START
MANAGEMENT_URL_PREFIX = {'manager': MANAGER_PREFIX,
                         'operator': OPERATOR_PREFIX,
                         'user': USER_PREFIX}
# Do not edit! - END

# ticket competence abandoned
NO_MORE_COMPETENCE_OVER_TICKET = _("Nessuna competenza sul ticket")
# ticket readonly access
READONLY_COMPETENCE_OVER_TICKET = _("Hai accesso al ticket in sola lettura")

# min ticket content length (digits) to compress
TICKET_MIN_DIGITS_TO_COMPRESS = 90

# Access level to categories
# Override for your own context

# This parameters define the roles of users to open ticket
# If True, an employee is a user that has this parameter filled (in user model)
# If False, an employee is a user that is mapped as OrganizationalStructureOfficeEmployee
EMPLOYEE_ATTRIBUTE_NAME = 'matricola_dipendente'
EMPLOYEE_ATTRIBUTE_LABEL = 'Matricola dipendente'
# Label
ORGANIZATION_EMPLOYEE_LABEL = 'Dipendenti'
# If True, an internal user (not guest) is a user that has this filled (in user model)
# If False, an internal user is a user that is mapped as OrganizationalStructureOfficeEmployee
USER_ATTRIBUTE_NAME = 'matricola_studente'
USER_ATTRIBUTE_LABEL = 'Matricola studente'
# Label
ORGANIZATION_USER_LABEL = 'Studenti'


# E-mail messages
MSG_HEADER = _("""Gentile {user},
questo messaggio è stato inviato da {hostname}.
Per favore non rispondere a questa email.

-------------------

""")

MSG_FOOTER = _("""

-------------------

Per problemi tecnici contatta il nostro staff.
Cordiali saluti.
""")

UNAVAILABLE_TICKET_CATEGORY = _("""La tipologia di richiesta non è attiva""")

NEW_TICKET_CREATED_ALERT = _("""Ticket "{}" creato con successo""")

NEW_TICKET_CREATED = _("""{added_text}

L'identificativo univoco di questa transazione è {ticket}.

Clicca qui {url} per prenderne visione.""")

TICKET_UPDATED = _("""Il ticket "{ticket}" è stato aggiornato con il seguente messaggio:

{message}""")

USER_TICKET_MESSAGE = _("""Hai {status} un messaggio per il ticket \"{ticket}\"

Oggetto: {message_subject}

Testo: {message_text}

Clicca qui {url} per aprire il pannello dei messaggi.""")

TICKET_DELETED = _("""Il ticket "{ticket}" è stato eliminato correttamente.""")

SUMMARY_USER_EMAIL = _("""Il seguente ticket {event msg}:

{ticket}""")

SUMMARY_EMPLOYEE_EMAIL = _("""Ci sono {opened_ticket_number} tickets da gestire.

{tickets_per_office}""")

NEW_TICKET_CREATED_EMPLOYEE_BODY = _("""E' stata effettuata una nuova richiesta all'ufficio {destination_office}.

Utente: {ticket_user}
Oggetto: {ticket_subject}
Descrizione: {ticket_description}

URL: {ticket_url}""")


# Old english version
NEW_TICKET_UPDATE_OLD_EN = _("Dear {user},"
                      "you have successfully {status} the ticket:"
                      ""
                      "{ticket}"
                      ""
                      "This message was sent to you by {hostname}."
                      "Please do not reply to this email.")

USER_TICKET_MESSAGE_OLD_EN = _("Dear {user},"
                       "you have successfully {status} a message for ticket:"
                       ""
                       "{ticket}"
                       ""
                       "This message was sent to you by {hostname}."
                       "Please do not reply to this email.")

TICKET_UPDATED_OLD_EN = _("Dear {user},"
                   "the ticket:"
                   ""
                   "{ticket}"
                   ""
                   "has been updated with the message:"
                   ""
                   "{message}."
                   ""
                   "This message was sent to you by {hostname}."
                   "Please do not reply to this email.")

SUMMARY_USER_EMAIL_OLD_EN = _("Dear {user},"
                       "the following ticket {event_msg}:"
                       ""
                       "{ticket}"
                       ""
                       "This message was sent to you by {hostname}."
                       "Please do not reply to this email.")

SUMMARY_EMPLOYEE_EMAIL_OLD_EN = _("Dear {user},"
                           "You have {open_ticket_number} tickets to manage."
                           ""
                           "{tickets_per_office}"
                           ""
                           "This message was sent to you by {hostname}."
                           "Please do not reply to this email.")
