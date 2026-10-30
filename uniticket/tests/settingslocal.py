# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases



# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ALLOWED_HOSTS = ['*']

ADMIN_PATH = 'admin'

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

    'datatables_ajax',

    'uni_ticket_bootstrap_italia_template',
    # 'django_unical_bootstrap_italia',
    'bootstrap_italia_template',

    #'bootstrapform',
    'uni_ticket',
    'django_form_builder',
    'nested_admin',
    'organizational_area',

    # interfaccia con App IO
    'app_io',

    # Django Rest
    'rest_framework',
    # 'rest_framework.authtoken',
    'api_rest',

    # Django channels and chat
    'channels',
    # 'chat',

    ##SAML2 SP
    # 'djangosaml2',
    # 'saml2_sp',
]

# chat app settings
if 'chat' in INSTALLED_APPS:
    from chat.settings import *

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
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'api_rest.authorizations.AuthorizationToken',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_PAGINATION_CLASS':
        'api_rest.pagination.StandardPagination',
    'PAGE_SIZE': 5
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
