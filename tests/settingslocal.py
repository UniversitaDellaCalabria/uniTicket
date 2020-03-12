# Database
# https://docs.djangoproject.com/en/2.1/ref/settings/#databases

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'rz82a_#y1#s=l+loeqgn_4xslwchu%yxtpdf)h7b$6kn+p+=+^'

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
    'bootstrap_italia_template',
    'django_unical_bootstrap_italia',

    'bootstrapform',
    'uni_ticket',
    'django_form_builder',
    'nested_admin',
    'organizational_area',

    # Django Rest
    'rest_framework',

    ##SAML2 SP
    # 'djangosaml2',
    # 'saml2_sp',
]


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

# This parameters define the roles of users to open ticket
# If True, an employee is a user that has this parameter filled (in user model)
# If False, an employee is a user that is mapped as OrganizationalStructureOfficeEmployee
EMPLOYEE_ATTRIBUTE_NAME = 'matricola_dipendente'
# If True, an internal user (not guest) is a user that has this filled (in user model)
# If False, an internal user is a user that is mapped as OrganizationalStructureOfficeEmployee
USER_ATTRIBUTE_NAME = 'matricola_studente'

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
