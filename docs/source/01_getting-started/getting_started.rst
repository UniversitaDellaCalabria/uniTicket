.. django-form-builder documentation master file, created by
   sphinx-quickstart on Tue Jul  2 08:50:49 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Requisiti
=========

.. code-block:: python

    sudo apt install xmlsec1 mariadb-server libmariadbclient-dev python3-dev python3-pip libssl-dev libmariadb-dev-compat libsasl2-dev libldap2-dev

    pip3 install virtualenv
    virtualenv -ppython3 helpdesk.env
    source helpdesk.env/bin/activate

Download del software e dipendenze
==================================

.. code-block:: python

    git clone https://github.com/UniversitaDellaCalabria/uniTicket.git
    cd uniTicket
    pip3 install -r requirements

Setup parametri
===============

.. code-block:: python

    cd uni_ticket_project

    # copy and modify as your needs
    cp settingslocal.py.example settingslocal.py

Nel file di configurazione generale **uni_ticket_project/settingslocal.py** è possibile:

- Definire il model da utilizzare per la gestione degli utenti

.. code-block:: python

    # user model fpr auth
    AUTH_USER_MODEL = "accounts.User"

- Definire i parametri per la localizzazione

.. code-block:: python

    # localization
    LANGUAGE_CODE = 'it'
    TIME_ZONE = 'Europe/Rome'

- Definire i formati delle date da utilizzare

.. code-block:: python

    DEFAULT_DATE_FORMAT = '%Y-%m-%d'
    DEFAULT_DATETIME_FORMAT = '{} %H:%M'.format(DEFAULT_DATE_FORMAT)
    DATE_INPUT_FORMATS = [DEFAULT_DATE_FORMAT, '%d/%m/%Y']

- Definire l'ADMIN_PATH
- Definire i database e l'hostname
- Le app installate (INSTALLED_APPS)

- Selezionare i widget da applicare ai campi dei form

.. code-block:: python

    CUSTOM_WIDGETS = {
        'BaseDateField': 'bootstrap_italia_template.widgets.BootstrapItaliaDateWidget',
        # 'BaseDateTimeField': 'bootstrap_italia_template.widgets.BootstrapItaliaTimeWidget',
        #'CustomSelectBoxField': 'bootstrap_italia_template.widgets.BootstrapItaliaSelectWidget',
        'CustomRadioBoxField': 'bootstrap_italia_template.widgets.BootstrapItaliaRadioWidget',
        # 'BaseDateField': 'django.forms.widgets.DateInput',
        # 'DateField': 'django.forms.widgets.DateInput',
        # 'CustomSelectBoxField': 'django.forms.widgets.Select',
        # 'CustomRadioBoxField': 'django.forms.widgets.RadioSelect',
    }

- Definire parametri relativi alla configurazione delle app "chat" e "channels"

.. code-block:: python

    # chat: message to load in a conversation from history
    MESSAGES_TO_LOAD = 1500

    if "channels" in INSTALLED_APPS:
    ASGI_APPLICATION = 'uni_ticket_project.routing.application'
    CHANNEL_LAYERS = {
        'default': {
            'BACKEND': 'channels_redis.core.RedisChannelLayer',
            'CONFIG': {
                "hosts": [('127.0.0.1', 6379)],
            },
        },
    }

- Definire i parametri per la criptazione basata su RSA dei token che viaggiano negli URL

.. code-block:: python

    # UNITICKET JWE support
    UNITICKET_JWE_RSA_KEY_PATH = 'saml2_sp/saml2_config/certificates/key.pem'
    UNITICKET_JWE_ALG = "RSA1_5"
    UNITICKET_JWE_ENC = "A128CBC-HS256"
    # end JWE support

- Definire *secret_key* e *salt* per la criptazione del codice CAPTCHA

.. code-block:: python

    # CAPTCHA encryption
    ENCRYPTION_SECRET = b'secret'
    ENCRYPTION_SALT = b'salt'

Nel file di configurazione **uni_ticket/settings.py** è possibile individuare (ed eventualmente sovrascrivere in *settingslocal.py*):

- I nomi delle cartelle nelle quali verranno conservati gli allegati

.. code-block:: python

    # system attachments folders
    LOGOS_FOLDER = 'logos'
    STRUCTURES_FOLDER = 'structures'
    TICKET_ATTACHMENT_FOLDER = 'ticket'
    TICKET_CATEGORIES_FOLDER = 'categories'
    TICKET_MESSAGES_ATTACHMENT_SUBFOLDER = 'messages'
    TICKET_TASK_ATTACHMENT_SUBFOLDER = 'task'
    CATEGORY_CONDITIONS_ATTACHMENT_SUBFOLDER = 'conditions'

- Il parametro che consente di mostrare la priorità dei ticket agli utenti

.. code-block:: python

    # show ticket priority to simple userse
    SIMPLE_USER_SHOW_PRIORITY = False

- ID e Label del checkbox di accettazione delle clausole obbligatorie

.. code-block:: python

    # category conditions form field
    TICKET_CONDITIONS_FIELD_ID = 'condizioni_field_id'
    TICKET_CONDITIONS_TEXT = _('Dichiara altresì di aver letto '
                               'e compreso quanto scritto sopra '
                               'e di assumere ogni responsabilità '
                               'su quanto di seguito dichiarato')

- La denominazione dei campi *oggetto* e *descrizione* dei form per la creazione dei ticket

.. code-block:: python

    # new ticket heading text (user informations)
    SHOW_HEADING_TEXT = True
    TICKET_HEADING_TEXT = _('Soggetto richiedente: <b>{user}</b>'
                            '<br><span class="x-small">[{taxpayer}]</span>')

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

- I livelli di priorità da assegnare ai ticket

.. code-block:: python

    PRIORITY_LEVELS = (
                        ('-2',_('Molto alta')),
                        ('-1',_('Alta')),
                        ('0',_('Normale')),
                        ('1',_('Bassa')),
                        ('2',_('Molto bassa')),
                      )

- La soglia massima di ticket giornalieri per utente

.. code-block:: python

    # 0 = unlimited
    MAX_DAILY_TICKET_PER_USER = 10

- La denominazione di ogni tipologia di utente per la definizione degli URL

.. code-block:: python

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

- Le definizioni per competenza abbandonata/sola lettura

.. code-block:: python

    # ticket competence abandoned
    NO_MORE_COMPETENCE_OVER_TICKET = _("Nessuna competenza sul ticket")
    # ticket readonly access
    READONLY_COMPETENCE_OVER_TICKET = _("Hai accesso al ticket in sola lettura")

- Il numero minimo di digits per la compressione del contenuto di un ticket

.. code-block:: python

    # min ticket content length (digits) to compress
    TICKET_MIN_DIGITS_TO_COMPRESS = 90

- La definizione degli utenti "employee" e "internal user" in base al tipo di organizzazione (università o altro)

.. code-block:: python

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

- I testi delle email che il sistema invia agli utenti

Creazione Database
==================

.. code-block:: python

    # create your MysqlDB
    export USER='that-user'
    export PASS='that-password'
    export HOST='%'
    export DB='uniauth'

    # tested on Debian 10
    sudo mysql -u root -e "\
    CREATE USER IF NOT EXISTS '${USER}'@'${HOST}' IDENTIFIED BY '${PASS}';\
    CREATE DATABASE IF NOT EXISTS ${DB} CHARACTER SET = 'utf8' COLLATE = 'utf8_general_ci';\
    GRANT ALL PRIVILEGES ON ${DB}.* TO '${USER}'@'${HOST}';"

Creazione tabelle e superuser
=============================

.. code-block:: python

    ./manage.py migrate
    ./manage.py createsuperuser

Run
===

.. code-block:: python

    ./manage.py runserver

Produzione
==========

Ricorda di eseguire compilescss collectstatic per compilare e copiare tutti i file statici nelle cartelle di produzione:

.. code-block:: python

    ./manage.py compilescss
    ./manage.py collectstatic

Per un ulteriore controllo in fase di debug è possibile utilizzare i comandi seguenti con uwsgi:

.. code-block:: python

    /etc/init.d/uni_ticket stop
    uwsgi --ini /opt/uni_ticket/uwsgi_setup/uwsgi.ini.debug
