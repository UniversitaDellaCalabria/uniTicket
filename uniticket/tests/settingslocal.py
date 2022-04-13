# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases



# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = ['*']

ADMIN_PATH = 'gestione'

HOSTNAME = 'ticket.unical.it'
EMAIL_SENDER = 'no-reply@{}'.format(HOSTNAME)
INTERNAL_IPS = ['127.0.0.1']


# Application definition
INSTALLED_APPS = [
    'accounts',

    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',

    'ckeditor',
    'datatables_ajax',

    'sass_processor',
    'uni_ticket_bootstrap_italia_template',
    'django_unical_bootstrap_italia',
    'bootstrap_italia_template',

    #'bootstrapform',
    'uni_ticket',
    'django_form_builder',
    'nested_admin',
    'organizational_area',

    # Django Rest
    'rest_framework',
    'api_rest',

    # Django channels and chat
    'channels',
    'chat',

    ##SAML2 SP
    # 'djangosaml2',
    # 'saml2_sp',
]

# chat app settings
if 'chat' in INSTALLED_APPS:
    pass

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

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 100
}

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


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        'djangosaml2': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
        'my_logger': {
                'handlers': ['console'],
                'propagate': True,
                'level': 'INFO',
            },
    }
}

# UNITICKET JWE support
UNITICKET_JWE_RSA_KEY_PATH = 'tests/certificates/private.key'
# end JWE support

# PROTOCOLLO, questi valori possono variare sulla base di come
# vengono istruite le pratiche all'interno del sistema di protocollo di riferimento

# from archipro_ws.settings import *

PROTOCOL_PACKAGE = 'titulus_ws' # archipro_ws
PROTOCOL_CLASS = f'{PROTOCOL_PACKAGE}.protocollo'
PROTOCOL_UTILS = f'{PROTOCOL_PACKAGE}.utils'

# DEFAULT EMAIL
PROTOCOL_EMAIL_DEFAULT = 'default@example.pec.it'

# TEST PARAMS
PROTOCOL_TEST_AOO = 'test_aoo_value'
PROTOCOL_TEST_FASCICOLO = 'test_fascicolo_value'
PROTOCOL_TEST_FASCICOLO_ANNO = 'test_fascicolo_anno_value'
PROTOCOL_TEST_AGD = 'test_agd_value'
PROTOCOL_TEST_UO = 'test_uo_value'
PROTOCOL_TEST_UO_RPA = 'test_uo_rpa_value'
PROTOCOL_TEST_TITOLARIO = 'test_titolario_value'

# ENDPOINTS (TEST AND PRODUCTION)
PROTOCOL_TEST_URL = 'URL_TEST' # test
PROTOCOL_URL = 'URL_PROD' # production

# TEST CREDENTIALS
PROTOCOL_TEST_LOGIN = 'TEST_LOGIN'
PROTOCOL_TEST_PASSW = 'TEST_PASSWORD'

# XML flusso ArchiPRO
PROTOCOL_XML = """<Segnatura xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema">
<Intestazione>
<Oggetto>{oggetto}</Oggetto>
<Identificatore>
<CodiceAmministrazione>UNICAL</CodiceAmministrazione>
<CodiceAOO>{aoo}</CodiceAOO>
<Flusso>E</Flusso>
</Identificatore>
<Mittente>

<Dipendente id="{identificativo_dipendente}">
<Denominazione>{denominazione_persona}</Denominazione>
</Dipendente>

<Studente id="{identificativo_utente}">
<Denominazione>{denominazione_persona}</Denominazione>
</Studente>

<Persona id="{id_persona}">
<Nome>{nome_persona}</Nome>
<Cognome>{cognome_persona}</Cognome>
</Persona>

</Mittente>
<Destinatario>
<Amministrazione>
<Denominazione>UNICAL</Denominazione>
<CodiceAmministrazione>UNICAL</CodiceAmministrazione>
<IndirizzoTelematico tipo="smtp">{email}</IndirizzoTelematico>
<UnitaOrganizzativa id=""/>
</Amministrazione>
</Destinatario>
<Classifica>
<CodiceTitolario>{id_titolario}</CodiceTitolario>
</Classifica>
<!--  Informazioni sul fascicolo  -->
<Fascicolo numero="{fascicolo_numero}" anno="{fascicolo_anno}"/>
</Intestazione>
<Descrizione>
<Documento id="1" nome="{nome_doc}">
<DescrizioneDocumento>{nome_doc}</DescrizioneDocumento>
<TipoDocumento>{tipo_doc}</TipoDocumento>
</Documento>
<Allegati>
<!-- Allegati -->
</Allegati>
</Descrizione>
<ApplicativoProtocollo nome="ArchiPRO">
<Parametro nome="agd" valore="{agd}"/>
<Parametro nome="uo" valore="{uo}"/>
</ApplicativoProtocollo>
</Segnatura>
"""

# XML flusso Titulus
PROTOCOL_XML = """
<doc tipo="arrivo" cod_amm_aoo="{cod_amm_aoo}">
    <autore>{autore}</autore>
    <oggetto>{oggetto}</oggetto>
    <classif cod="{cod_classif}">{classif}</classif>
    <allegato>{allegato}</allegato>
    <rif_interni>
		<rif_interno diritto="RPA"
                     nome_persona="{nome_persona_rif_interno}"
                     nome_uff="{nome_uff_rif_interno}"
                     cod_uff="{cod_uff_rif_interno}"/>
    </rif_interni>
    <rif_esterni>
        <rif_esterno codice_fiscale="{codice_fiscale_rif_esterno}">
            <nome cod="{cod_nome_rif_esterno}">
                {nome_rif_esterno}
            </nome>
            <indirizzo email="{email_rif_esterno}"
                       fax="{fax_rif_esterno}"
                       tel="{tel_rif_esterno}"
                       xml:space="preserve">
                {indirizzo}
            </indirizzo>
        </rif_esterno>
    </rif_esterni>
</doc>

"""
# END PROTOCOLLO


