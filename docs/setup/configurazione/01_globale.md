# Configurazione globale

## Creazione del settingslocal.py

    cd uni_ticket_project
    # copy and modify as your needs
    cp settingslocal.py.example settingslocal.py

## User model

Model da utilizzare per la gestione degli utenti

    # user model fpr auth
    AUTH_USER_MODEL = "accounts.User"

## Formato date e datetime

Formati delle date da utilizzare

    DEFAULT_DATE_FORMAT = '%Y-%m-%d'
    DEFAULT_DATETIME_FORMAT = '{} %H:%M'.format(DEFAULT_DATE_FORMAT)
    DATE_INPUT_FORMATS = [DEFAULT_DATE_FORMAT, '%d/%m/%Y']

    # override globals
    DATE_INPUT_FORMATS = [DEFAULT_DATE_FORMAT, '%Y-%m-%d']
    DATETIME_INPUT_FORMATS = [DEFAULT_DATETIME_FORMAT, f'%Y-%m-%d {DEFAULT_TIME_FORMAT}']

    # for javascript datepickers
    # BootstrapItalia datepicker
    JS_DEFAULT_DATE_FORMAT = "dd/MM/yyyy"
    # Cutstom datetimepicker
    JS_DEFAULT_DATETIME_FORMAT = 'DD/MM/Y hh:mm'

## Admin path

Path per l'accesso al backend

    ADMIN_PATH = "custom_path"

## Database

Definizione dei database

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': 'uniauth',
            'HOST': 'localhost',
            'USER': 'that-user',
            'PASSWORD': 'that-password',
            'PORT': '',
            'OPTIONS': {'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"}
        },
    }

## Form custom widgets

Selezionare i widget da applicare ai campi dei form

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

## Channels e chat

Parametri relativi alla configurazione delle app «chat» e «channels»

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

## Criptazione URL token

Parametri per la criptazione basata su RSA dei token che viaggiano negli URL

    # UNITICKET JWE support
    UNITICKET_JWE_RSA_KEY_PATH = 'saml2_sp/saml2_config/certificates/key.pem'
    UNITICKET_JWE_ALG = "RSA-OAEP"
    UNITICKET_JWE_ENC = "A128CBC-HS256"
    # end JWE support

## Captcha

Secret_key e salt per la criptazione del codice CAPTCHA

    # CAPTCHA encryption
    CAPTCHA_SECRET = b'secret'
    CAPTCHA_SALT = b'salt'
    # end CAPTCHA encryption

Scadenza codice captcha

    CAPTCHA_EXPIRATION_TIME = 45000 # milliseconds

## Privilegi superuser

Consentire ai super utenti Django di accedere a tutte le strutture in frontend

    # superusers view all
    SUPER_USER_VIEW_ALL = True

## Localizzazione

Parametri per la localizzazione

    # Internationalization
    # Set to False to avoid problems with javascript datepickers
    # (that use the DATE_INPUT_FORMATS and DATETIME_INPUT_FORMATS)
    # The template uses {% localize on %} tag to localize dates
    USE_L10N = False

    # localization
    LANGUAGES = (
    ('it', _('Italiano')),
    ('en', _('Inglese')),
    )

    LANGUAGE_CODE = 'it'
    LOCALE_PATHS = (
        os.path.join(BASE_DIR, "locale"),
    )

    TIME_ZONE = 'Europe/Rome'