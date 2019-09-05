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

    git clone git@bitbucket.org:unical-ict-dev/django-helpdesk.git
    cd django-helpdesk
    pip3 install -r requirements

Setup parametri
===============

.. code-block:: python

    cd django-helpdesk

    # copy and modify as your needs
    cp settingslocal.py.example settingslocal.py

Nel file di configurazione generale **django-helpdesk/settings.py** è possibile:

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

- Gestire la definizione degli utenti "employee" in base al tipo di organizzazione

.. code-block:: python

    # This parameter defines the roles of users to open ticket
    # If True, an employee is a user that has the parameter 'matricola_dipendente' filled
    # If False, an employee is a user that is mapped as OrganizationalStructureOfficeEmployee
    IS_UNIVERSITY = True

Nel file di configurazione **uni_ticket/settings.py** è possibile:

- Definire i nomi delle cartelle nelle quali verranno conservati gli allegati

.. code-block:: python

    TICKET_FOLDER = 'ticket'
    TICKET_REPLY_ATTACHMENT_SUBFOLDER = 'updates'
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
    
    # Accesso sul ticket in sola lettura
    NO_MORE_COMPETENCE_OVER_TICKET = _("Hai accesso sul ticket in sola lettura")

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

    /etc/init.d/django-helpdesk stop
    uwsgi --ini /opt/django-helpdesk/uwsgi_setup/uwsgi.ini.debug



