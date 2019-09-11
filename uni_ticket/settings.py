from django.utils.translation import gettext as _

TICKET_FOLDER = 'ticket'
TICKET_REPLY_ATTACHMENT_SUBFOLDER = 'updates'
TICKET_TASK_ATTACHMENT_SUBFOLDER = 'task'

TICKET_CONDITIONS_FIELD_ID = 'condizioni_field_id'
TICKET_CONDITIONS_TEXT = _('Ho letto e compreso quanto scritto sopra')

TICKET_SUBJECT_ID = 'ticket_subject'
TICKET_SUBJECT_LABEL = _('Oggetto')
TICKET_SUBJECT_HELP_TEXT = _('Oggetto del Ticket')

TICKET_DESCRIPTION_ID = 'ticket_description'
TICKET_DESCRIPTION_LABEL = _('Descrizione')
TICKET_DESCRIPTION_HELP_TEXT = ('Descrizione del Ticket')

PRIORITY_LEVELS = (
                    ('-2',_('Molto alta')),
                    ('-1',_('Alta')),
                    ('0',_('Normale')),
                    ('1',_('Bassa')),
                    ('2',_('Molto bassa')),
                  )

# 0 = unlimited
MAX_DAILY_TICKET_PER_USER = 10

CONTEXT_SIMPLE_USER = _('Utente semplice')
# To change the URLs prefix for every user type
MANAGER_PREFIX = 'Manager'
OPERATOR_PREFIX = 'Operatore'
USER_PREFIX = 'user'

# Do not edit! - START
MANAGEMENT_URL_PREFIX = {'manager': MANAGER_PREFIX,
                         'operator': OPERATOR_PREFIX,
                         'user': USER_PREFIX}
# Do not edit! - END

# Competenza sul ticket abbandonata
NO_MORE_COMPETENCE_OVER_TICKET = _("Nessuna competenza sul ticket")
# Accesso sul ticket in sola lettura
READONLY_COMPETENCE_OVER_TICKET = _("Hai accesso al ticket in sola lettura")

SUMMARY_USER_EMAIL = _("Dear {user},"
                       "the following ticket {event_msg}:"
                       ""
                       "{ticket}"
                       ""
                       "This message was sent to you by {hostname}."
                       "Please do not reply to this email.")

SUMMARY_EMPLOYEE_EMAIL = _("Dear {user},"
                           "You have {open_ticket_number} tickets to manage."
                           ""
                           "{tickets_per_office}"
                           ""
                           "This message was sent to you by {hostname}."
                           "Please do not reply to this email.")
