# Override impostazioni di default

## Cartelle allegati

Cartelle nelle quali verranno conservati gli allegati

    # system attachments folders
    LOGOS_FOLDER = 'logos'
    STRUCTURES_FOLDER = 'structures'
    TICKET_ATTACHMENT_FOLDER = 'ticket'
    TICKET_CATEGORIES_FOLDER = 'categories'
    TICKET_MESSAGES_ATTACHMENT_SUBFOLDER = 'messages'
    TICKET_TASK_ATTACHMENT_SUBFOLDER = 'task'
    CATEGORY_CONDITIONS_ATTACHMENT_SUBFOLDER = 'conditions'

## Priorità visibile agli utenti

Consente di mostrare la priorità dei ticket agli utenti

    # show ticket priority to simple userse
    SIMPLE_USER_SHOW_PRIORITY = False

## Clausole obbligatorie

ID e Label del checkbox di accettazione delle clausole obbligatorie

    # category conditions form field
    TICKET_CONDITIONS_FIELD_ID = 'condizioni_field_id'
    TICKET_CONDITIONS_TEXT = _('Dichiara altresì di aver letto '
                            'e compreso quanto scritto sopra '
                            'e di assumere ogni responsabilità '
                            'su quanto di seguito dichiarato')

## Campi "oggetto" e "descrizione"

Denominazione dei campi oggetto e descrizione dei form per la creazione dei ticket

    # new ticket static form fields
    # ticket subject
    TICKET_SUBJECT_ID = 'ticket_subject'
    TICKET_SUBJECT_LABEL = _('Oggetto della Richiesta')
    TICKET_SUBJECT_HELP_TEXT = _("Ulteriore specificazione o "
                                "personalizzazione dell'Oggetto della Richiesta")

    # ticket description
    TICKET_DESCRIPTION_ID = 'ticket_description'
    TICKET_DESCRIPTION_LABEL = _('Descrizione')
    TICKET_DESCRIPTION_HELP_TEXT = ('Ulteriore Descrizione della Richiesta, '
                                    'eventuali note del Richiedente')

## ???

    # new ticket heading text (user informations)
    SHOW_HEADING_TEXT = True
    TICKET_HEADING_TEXT = _('Soggetto richiedente: <b>{user}</b>'
                            '<br><span class="x-small">[{taxpayer}]</span>')

## Livelli di priorità

I livelli di priorità da assegnare ai ticket

    PRIORITY_LEVELS = (
        ('-2',_('Molto alta')),
        ('-1',_('Alta')),
        ('0',_('Normale')),
        ('1',_('Bassa')),
        ('2',_('Molto bassa')),
    )

## Limite ticket giornalieri

La soglia massima di ticket giornalieri per utente

    # 0 = unlimited
    MAX_DAILY_TICKET_PER_USER = 10

## URL path ruoli

La denominazione di ogni tipologia di utente per la definizione degli URL

    # user contexts
    CONTEXT_SIMPLE_USER = _('Utente')

    # To change the URLs prefix for every user type
    MANAGER_PREFIX = 'Manager'
    OPERATOR_PREFIX = 'Operatore'
    USER_PREFIX = 'User'

## Definizioni alert

Competenza abbandonata/sola lettura

    # ticket competence abandoned
    NO_MORE_COMPETENCE_OVER_TICKET = _("Nessuna competenza sul ticket")
    # ticket readonly access
    READONLY_COMPETENCE_OVER_TICKET = _("Hai accesso al ticket in sola lettura")

## Soglia compressione ticket

Il numero minimo di digits per la compressione del contenuto di un ticket nel DB

    # min ticket content length (digits) to compress
    TICKET_MIN_DIGITS_TO_COMPRESS = 90

## Utenti employee e internal user

Definizione degli utenti «employee» e «internal user» in base al tipo di organizzazione (università o altro)

    # This parameters define the roles of users to open ticket
    # If True, an employee is a user that has this parameter filled (in user model)
    # If False, an employee is a user that is mapped as OrganizationalStructureOfficeEmployee
    EMPLOYEE_ATTRIBUTE_NAME = 'identificativo_dipendente'
    EMPLOYEE_ATTRIBUTE_LABEL = 'Matricola dipendente'
    # Label
    ORGANIZATION_EMPLOYEE_LABEL = 'Dipendenti'
    # If True, an internal user (not guest) is a user that has this filled (in user model)
    # If False, an internal user is a user that is mapped as OrganizationalStructureOfficeEmployee
    USER_ATTRIBUTE_NAME = 'identificativo_utente'
    USER_ATTRIBUTE_LABEL = 'Matricola studente'
    # Label
    ORGANIZATION_USER_LABEL = 'Studenti'

## ?? testi email

I testi delle email che il sistema invia agli utenti