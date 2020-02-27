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

Nel file di configurazione generale **uni_ticket_project/settings.py** è possibile:

- Definire i formati delle date da utilizzare

.. code-block:: python

    DEFAULT_DATE_FORMAT = '%Y-%m-%d'
    DEFAULT_DATETIME_FORMAT = '{} %H:%M'.format(DEFAULT_DATE_FORMAT)
    DATE_INPUT_FORMATS = [DEFAULT_DATE_FORMAT, '%d/%m/%Y']

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

- Gestire la definizione degli utenti "employee" e "internal user" in base al tipo di organizzazione (università o altro)

.. code-block:: python

    # This parameters define the roles of users to open ticket
    # If True, an employee is a user that has this parameter filled
    # If False, an employee is a user that is mapped as OrganizationalStructureOfficeEmployee
    EMPLOYEE_ATTRIBUTE_NAME = 'matricola_dipendente'
    # If True, an internal user (not guest) is a user that has this filled
    # If False, an internal user is a user that is mapped as OrganizationalStructureOfficeEmployee
    USER_ATTRIBUTE_NAME = 'matricola_studente'

Nel file di configurazione **uni_ticket/settings.py** è possibile:

- Definire i nomi delle cartelle nelle quali verranno conservati gli allegati

.. code-block:: python

    TICKET_ATTACHMENT_FOLDER = 'ticket'
    TICKET_MESSAGES_ATTACHMENT_SUBFOLDER = 'updates'
    TICKET_TASK_ATTACHMENT_SUBFOLDER = 'task'

- Modificare ID e Label del checkbox di accettazione delle clausole obbligatorie

.. code-block:: python

    TICKET_CONDITIONS_FIELD_ID = 'condizioni_field_id'
    TICKET_CONDITIONS_TEXT = _('Ho letto e compreso quanto scritto sopra')

- Modificare la denominazione dei campi *oggetto* e *descrizione* dei form per la creazione dei ticket

.. code-block:: python

    TICKET_SUBJECT_ID = 'ticket_subject'
    TICKET_SUBJECT_LABEL = _('Oggetto')
    TICKET_SUBJECT_HELP_TEXT = _('Oggetto del Ticket')

    TICKET_DESCRIPTION_ID = 'ticket_description'
    TICKET_DESCRIPTION_LABEL = _('Descrizione')
    TICKET_DESCRIPTION_HELP_TEXT = ('Descrizione del Ticket')

- Definire i livelli di priorità da assegnare ai ticket

.. code-block:: python

    PRIORITY_LEVELS = (
                        ('-2',_('Molto alta')),
                        ('-1',_('Alta')),
                        ('0',_('Normale')),
                        ('1',_('Bassa')),
                        ('2',_('Molto bassa')),
                      )

- Stabilire una soglia massima di ticket giornalieri per utente

.. code-block:: python

    # 0 = unlimited
    MAX_DAILY_TICKET_PER_USER = 10

- Modificare la denominazione di ogni tipologia di utente per la definizione degli URL

.. code-block:: python

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

- Definizione dei testi da utilizzare

.. code-block:: python

    # Competenza sul ticket abbandonata
    NO_MORE_COMPETENCE_OVER_TICKET = _("Nessuna competenza sul ticket")
    # Accesso sul ticket in sola lettura
    READONLY_COMPETENCE_OVER_TICKET = _("Hai accesso al ticket in sola lettura")
    
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
    
    NEW_TICKET_CREATED = _("""Il ticket "{ticket}" è stato creato correttamente.
    
    Dati inseriti:
    {data}
    
    Files:
    {files}""")
    
    TICKET_UPDATED = _("""Il ticket "{ticket}" è stato aggiornato con il seguente messaggio:
    
    {message}""")
    
    USER_TICKET_MESSAGE = _("""Hai {status} un messaggio per il ticket \"{ticket}\"""")
    
    TICKET_DELETED = _("""Il ticket "{ticket}" è stato eliminato correttamente.""")
    
    SUMMARY_USER_EMAIL = _("""Il seguente ticket {event msg}:
    
    {ticket}""")
    
    SUMMARY_EMPLOYEE_EMAIL = _("""Hai {open_ticket_number} tickets da gestire.
    
    {tickets_per_office}""")

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

Ricorda di eseguire collectstatic per copiare tutti i file statici nelle cartelle di produzione:

.. code-block:: python

    ./manage.py collectstatic

Per un ulteriore controllo in fase di debug è possibile utilizzare i comandi seguenti con uwsgi:

.. code-block:: python

    /etc/init.d/uni_ticket stop
    uwsgi --ini /opt/uni_ticket/uwsgi_setup/uwsgi.ini.debug



