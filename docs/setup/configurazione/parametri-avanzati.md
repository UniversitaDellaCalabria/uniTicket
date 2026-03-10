# Configurazione Parametri Avanzati

Questa sezione descrive i parametri avanzati che influenzano il comportamento profondo di uniTicket. Queste impostazioni gestiscono l'architettura del sistema, i livelli di sicurezza, l'integrazione dei moduli esterni e l'ottimizzazione delle risorse server.

### User model
Definisce il modello personalizzato per la gestione degli utenti all'interno dell'applicazione. uniTicket utilizza un modello esteso per gestire attributi specifici richiesti dai flussi amministrativi.

``` py
# user model fpr auth
AUTH_USER_MODEL = "accounts.User"
```

### JWE

Configurazione degli algoritmi di cifratura per il supporto JSON Web Encryption (JWE). Questi parametri definiscono lo standard crittografico utilizzato per proteggere i token e le informazioni sensibili trasmesse tramite URL, garantendo comunicazioni stateless sicure.

``` py
UNITICKET_JWE_ALG = getattr(settings, "UNITICKET_JWE_ALG", "RSA-OAEP")
UNITICKET_JWE_ENC = getattr(settings, "UNITICKET_JWE_ENC", "A128CBC-HS256")
```

### Debug o produzione?

Questo blocco gestisce il passaggio cruciale tra l'ambiente di sviluppo e quello di produzione. Quando DEBUG è impostato su False, il sistema attiva rigide policy di sicurezza per cookie e sessioni (Secure, HttpOnly), abilita la protezione CSRF sui domini fidati e configura il protocollo sicuro (wss://) per le comunicazioni via WebSocket.

``` py
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
if not DEBUG:
    # Impostazioni di sicurezza della sessionie e dei cookie
    SESSION_EXPIRE_AT_BROWSER_CLOSE = True
    SESSION_COOKIE_AGE = (60*60)*9
    CSRF_COOKIE_HTTPONLY = True
    CSRF_COOKIE_SECURE = True
    CSRF_TRUSTED_ORIGINS = [f'https://{HOSTNAME}']
    SESSION_COOKIE_SECURE = True
    # protocollo WS per chat
    WS_PROTOCOL = 'wss://'
```

### Lista app installate

L'elenco INSTALLED_APPS registra tutti i moduli attivi nel sistema. Include i core di Django, i plugin per la UI (Bootstrap Italia), i motori di gestione form e gli strumenti avanzati come la chat (Channels), l'integrazione con l'App IO, il supporto Markdown e l'interfaccia REST API.

``` py
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
    #'django_unical_bootstrap_italia',
    'bootstrap_italia_template',
    'uni_ticket',
    'django_form_builder',
    'nested_admin',
    'organizational_area',
    'app_io',
    'rest_framework',
    'api_rest',
    'channels',
    'chat',
    'admin_adv_search_builder',
    'markdownx',
]
```

### Path dei template

Configura il motore di rendering dei template. Definisce le directory dove il sistema cerca i file HTML e i context_processors che iniettano variabili globali (come l'oggetto request o i messages) in ogni pagina renderizzata.

``` py
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
```

### Lista dei middleware

I middleware sono componenti che elaborano le richieste e le risposte a livello di sistema. Gestiscono la sicurezza, le sessioni, la localizzazione linguistica e le logiche specifiche di uniTicket relative ai profili utente.

``` py
MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "accounts.middlewares.AccountsChangeDataMiddleware",
]
```

### Path per file static, media e tmp

Definisce la struttura del file system per la gestione degli asset. Include la directory per i file statici (CSS/JS), l'area media per i documenti caricati dagli utenti e una cartella di cache temporanea necessaria per operazioni massive come la generazione di PDF o l'elaborazione di file pesanti.

``` py
# Static files (CSS, JavaScript, Images)
DATA_DIR = os.path.join(BASE_DIR, "data")

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(DATA_DIR, "static")
if not os.path.exists(STATIC_ROOT):
    pathlib.Path(STATIC_ROOT).mkdir(parents=True, exist_ok=True)

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(DATA_DIR, "media")
if not os.path.exists(MEDIA_ROOT):
    pathlib.Path(MEDIA_ROOT).mkdir(parents=True, exist_ok=True)

# used for pdf creation and other temporary files
CACHE_DIR = "uni_ticket_project_cache"
TMP_DIR = os.path.sep.join((BASE_DIR, CACHE_DIR, "tmp"))
if not os.path.exists(TMP_DIR):
    pathlib.Path(TMP_DIR).mkdir(parents=True, exist_ok=True)
```

### Custom widgets per i form

Associa i campi dei form generati dinamincamente ai widget grafici basati su Bootstrap Italia. Questo garantisce che ogni campo (date, select, radio) rispetti le linee guida AGID, mantenendo un'interfaccia coerente e accessibile.

``` py
CUSTOM_WIDGETS_IN_FORMSETS = False
CUSTOM_WIDGETS = {
    'BaseDateField': 'bootstrap_italia_template.widgets.BootstrapItaliaDateWidget',
    'BaseDateTimeSimpleField': 'uni_ticket_bootstrap_italia_template.widgets.UniTicketDateTimeWidget',
    'CustomSelectBoxField': 'bootstrap_italia_template.widgets.BootstrapItaliaSelectWidget',
    'CustomRadioBoxField': 'bootstrap_italia_template.widgets.BootstrapItaliaRadioWidget',
    'TextAreaField': forms.widgets.Textarea(attrs={"rows":2})
}
```

### Parametri per API REST

Configura il Django Rest Framework (DRF) per l'accesso programmatico ai dati. Definisce i metodi di autenticazione (anche tramite sistemi esterni), le classi di permesso per utenti autenticati e le logiche di paginazione dei risultati.

``` py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'uniticket_api_unical_authentication.authentication.UniTicketAPIUnicalAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated'
    ],
    'DEFAULT_PAGINATION_CLASS':
        'api_rest.pagination.StandardPagination',
    'PAGE_SIZE': 10
}
```

### Logging

Il sistema di logging permette il monitoraggio costante dell'applicazione. È configurato per inviare email agli amministratori in caso di errori critici in produzione e per registrare messaggi di debug sulla console per i moduli principali come uni_ticket, accounts e l'integrazione con il protocollo Titulus.

``` py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
    'verbose': {
        'format': '%(levelname)s [%(asctime)s] %(module)s %(message)s'
        },
    },
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
        'django.security.DisallowedHost': {
                'handlers': ['mail_admins'],
                'level': 'CRITICAL',
                'propagate': False,
        },
        'django': {
          'handlers': ['console','mail_admins'],
            'propagate': True,
            'level': 'ERROR',
        },
        'uni_ticket': {
            'handlers': ['console', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'titulus_ws': {
            'handlers': ['console', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'accounts': {
            'handlers': ['console', 'mail_admins'],
            'level': 'DEBUG',
            'propagate': True,
        },
    }
}
```

### IP interni

Specifica una lista di indirizzi IP considerati "interni" o sicuri, utili per visualizzare il debug toolbar (se installato) o per bypassare determinate restrizioni di accesso in fase di manutenzione.

``` py
INTERNAL_IPS = (
    '127.0.0.1',
)
```

### Gestione allegati

Definisce i filtri di sicurezza per il caricamento dei file. Specifica i MIME type ammessi per documenti, immagini e file firmati digitalmente (PDF/P7M), oltre a stabilire il limite massimo di dimensione per i caricamenti (es. 20MB) e la lunghezza massima dei nomi dei file.

``` py
# file validation
PDF_FILETYPE = ('application/pdf',)
DATA_FILETYPE = ('text/csv', 'application/json',
                 'application/vnd.ms-excel',
                 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                 'application/vnd.oasis.opendocument.spreadsheet',
                 'application/wps-office.xls',
                 'application/vnd.ms-powerpoint',
                 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                 )
TEXT_FILETYPE = ('text/plain',
                 'application/vnd.oasis.opendocument.text',
                 'application/msword',
                 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                )
IMG_FILETYPE = ('image/jpeg', 'image/png', 'image/gif', 'image/x-ms-bmp')
P7M_FILETYPE = ('application/pkcs7-mime',)
SIGNED_FILETYPE = PDF_FILETYPE + P7M_FILETYPE
PERMITTED_UPLOAD_FILETYPE = TEXT_FILETYPE + DATA_FILETYPE + IMG_FILETYPE + SIGNED_FILETYPE

# maximum permitted filename lengh in attachments, uploads
ATTACH_NAME_MAX_LEN = 100
MAX_UPLOAD_SIZE = 20971520
```

### Chat

Configura il motore di messaggistica real-time. Se il modulo channels è attivo, il sistema utilizza Redis come layer per gestire la comunicazione asincrona, definendo anche il numero massimo di messaggi da caricare dalla cronologia della conversazione.

``` py
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
```

### Localizzazione

Gestisce la lingua e il fuso orario del portale. Il sistema supporta l'internazionalizzazione (I18N) permettendo agli utenti di scegliere tra Italiano e Inglese, e imposta il fuso orario corretto per la registrazione temporale delle richieste.

``` py
# Internationalization
USE_L10N = False
USE_I18N = True
USE_TZ = True

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
```

### Safe paths e apps per account incompleto

Questi parametri definiscono le eccezioni alle restrizioni di accesso. Contengono gli URL (come il logout) e le app (come admin) che devono rimanere sempre accessibili anche se l'utente non ha ancora completato l'inserimento dei dati obbligatori nel proprio profilo.

``` py
SAFE_URL_PATHS = [LOGOUT_URL]  
SAFE_URL_APPS = ["admin", "accounts", "api_rest"])
```

### Markdown

Configurazione per il motore di elaborazione Markdown. Permette di limitare o abilitare specifici content type per l'upload di immagini e asset all'interno degli editor di testo.

``` py
# markdownX
MARKDOWNX_UPLOAD_CONTENT_TYPES = []
# END markdownx
```

### Modifica profilo utente

Questi due parametri definiscono i campi editabili (solitamente solo l'email se siamo in contesti di Single Sign-On che forniscono i dati al sistema) e quelli obbligatori, senza i quali, cioè, il profilo viene reputato incompleto.

``` py
EDITABLE_FIELDS = ["email",]  
REQUIRED_FIELDS = EDITABLE_FIELDS
```

### Vita del token per cambio email

Specifica la durata temporale (in minuti o secondi a seconda della logica di implementazione) del token di sicurezza inviato via email per confermare la variazione dell'indirizzo di posta elettronica dell'utente.

``` py
CHANGE_EMAIL_TOKEN_LIFE = 180
```

### Durata richieste precompilate

Imposta il periodo di validità (in giorni) per le richieste che sono state salvate come bozza ma non ancora sottomesse definitivamente. Oltre questo termine, le bozze possono essere rimosse per pulizia del database.

``` py
PRECOMPILED_TICKET_EXPIRE_DAYS = 180
```

### Campi "oggetto" e "descrizione"

Permette di personalizzare le etichette e i messaggi di aiuto per i campi fondamentali di ogni richiesta. Questa configurazione è vitale per adattare il linguaggio dell'interfaccia al target specifico dell'organizzazione (es. "Motivazione" invece di "Oggetto").

``` py
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
```

### Campo "captcha"

Parametri tecnici per l'integrazione del sistema CAPTCHA. Gestisce gli identificatori HTML e le etichette visibili che compongono il blocco di sicurezza per la validazione delle sottomissioni.

``` py
# captcha
TICKET_CAPTCHA_ID = getattr(
    settings, "TICKET_CAPTCHA_ID", "ticket_captcha"
)
TICKET_CAPTCHA_HIDDEN_ID = getattr(
    settings, "TICKET_CAPTCHA_HIDDEN_ID", "ticket_captcha_hidden"
)
TICKET_CAPTCHA_LABEL = getattr(
    settings, "TICKET_CAPTCHA_LABEL", _("Codice di verifica")
)
```

### Altri campi della richiesta

Configura gli elementi di interfaccia e i flag di sistema relativi alla creazione delle richieste. Include i nomi dei pulsanti di invio e i nomi dei campi utilizzati per tracciare chi ha compilato la richiesta e quando.

``` py
# new ticket submit buttons (create / generate import URL)
TICKET_CREATE_BUTTON_NAME = getattr(
    settings, "TICKET_CREATE_BUTTON_NAME", "confirm_submit"
)
TICKET_GENERATE_URL_BUTTON_NAME = getattr(
    settings, "TICKET_GENERATE_URL_BUTTON_NAME", "generate_url_submit"
)
TICKET_COMPILED_BY_USER_NAME = getattr(
    settings, "TICKET_COMPILED_BY_USER_NAME", "compiled_by_user"
)
TICKET_COMPILED_ONE_TIME_FLAG = getattr(
    settings, "TICKET_COMPILED_ONE_TIME_FLAG", "compiled_one_time"
)
TICKET_COMPILED_CREATION_DATE = getattr(
    settings, "TICKET_COMPILED_CREATION_DATE", "compiled_date"
)
TICKET_INPUT_MODULE_NAME = getattr(
    settings, "TICKET_INPUT_MODULE_NAME", "ticket_input_module"
)
```

### Soglia compressione richieste

Imposta la soglia dimensionale oltre la quale il contenuto testuale di una richiesta viene compresso prima del salvataggio nel database, ottimizzando le performance di archiviazione per testi molto lunghi.

``` py
# min ticket content length (digits) to compress
TICKET_MIN_DIGITS_TO_COMPRESS = 90
```

### URL path ruoli

Definisce i prefissi utilizzati negli URL per distinguere le aree operative. Questa impostazione è fondamentale per la corretta generazione dei percorsi di navigazione per manager, operatori e semplici utenti.

``` py
# user contexts
CONTEXT_SIMPLE_USER = getattr(settings, "CONTEXT_SIMPLE_USER", _("Utente"))

# Roles labels
MANAGER_PREFIX = getattr(settings, "MANAGER_PREFIX", "Manager")
OPERATOR_PREFIX = getattr(settings, "OPERATOR_PREFIX", "Operatore")
USER_PREFIX = getattr(settings, "USER_PREFIX", "user")
```

### Utenti employee e internal user

Gestisce la logica di mappatura dei ruoli basata sugli attributi del profilo utente. Permette di definire chi viene considerato "Dipendente" o "Studente" (internal user) e quali etichette devono essere mostrate nell'interfaccia o incluse nelle esportazioni dei dati in formato CSV.

``` py
# Access level to categories
EMPLOYEE_ATTRIBUTE_NAME = getattr(
    settings, "EMPLOYEE_ATTRIBUTE_NAME", "identificativo_dipendente"
)
EMPLOYEE_ATTRIBUTE_LABEL = getattr(
    settings, "EMPLOYEE_ATTRIBUTE_LABEL", "Matricola Dipendente"
)
ORGANIZATION_EMPLOYEE_LABEL = getattr(
    settings, "ORGANIZATION_EMPLOYEE_LABEL", "Dipendenti"
)
USER_ATTRIBUTE_NAME = getattr(
    settings, "USER_ATTRIBUTE_NAME", "identificativo_utente")
USER_ATTRIBUTE_LABEL = getattr(
    settings, "USER_ATTRIBUTE_LABEL", "Matricola utente")
ORGANIZATION_USER_LABEL = getattr(
    settings, "ORGANIZATION_USER_LABEL", "Studenti")
ADDITIONAL_USER_FIELDS = getattr(
    settings, "ADDITIONAL_USER_FIELDS", [
        EMPLOYEE_ATTRIBUTE_NAME,
        USER_ATTRIBUTE_NAME]
)
```