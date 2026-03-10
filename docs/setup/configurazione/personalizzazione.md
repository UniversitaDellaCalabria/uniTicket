# Personalizzazione

Questa sezione descrive i parametri opzionali che consentono di estendere o sovrascrivere le funzionalità di uniTicket e di adattare l'applicativo all'identità visiva e organizzativa della propria struttura. La modifica di questi valori permette una sintonizzazione fine del sistema senza intervenire sul core engine.

### Cartelle allegati

Definizione dell'alberatura delle directory all'interno del sistema di storage dove verranno archiviati i file caricati. La separazione in sotto-cartelle per messaggi, task e condizioni assicura un'organizzazione ordinata e performante dei file multimediali e dei documenti digitali.

``` py
# system attachments folders
TICKET_ATTACHMENT_FOLDER = getattr(
    settings, "TICKET_ATTACHMENT_FOLDER", "ticket")
TICKET_CATEGORIES_FOLDER = getattr(
    settings, "TICKET_CATEGORIES_FOLDER", "categories")
TICKET_MESSAGES_ATTACHMENT_SUBFOLDER = getattr(
    settings, "TICKET_MESSAGES_ATTACHMENT_SUBFOLDER", "messages"
)
TICKET_TASK_ATTACHMENT_SUBFOLDER = getattr(
    settings, "TICKET_TASK_ATTACHMENT_SUBFOLDER", "task"
)
CATEGORY_CONDITIONS_ATTACHMENT_SUBFOLDER = getattr(
    settings, "CATEGORY_CONDITIONS_ATTACHMENT_SUBFOLDER", "conditions"
)
```

### Privilegi superuser

Parametro booleano che determina il livello di visibilità globale per gli amministratori di sistema. Se attivo, permette ai super-utenti Django di bypassare le restrizioni per ufficio e visualizzare tutte le strutture organizzative direttamente dal frontend.

``` py
# superusers view all
SUPER_USER_VIEW_ALL = True
```

### Priorità visibile agli utenti

Regola la trasparenza del processo di gestione. Consente di decidere se l'utente finale (richiedente) può visualizzare il livello di urgenza assegnato alla propria richiesta o se tale informazione deve rimanere riservata esclusivamente agli operatori interni.

``` py
# show ticket priority to simple userse
SIMPLE_USER_SHOW_PRIORITY = False
```

### Clausole obbligatorie

Personalizzazione del campo di accettazione per le note legali e le clausole di responsabilità. Permette di definire l'ID tecnico del campo nel modulo e il testo (label) che l'utente deve confermare obbligatoriamente per procedere con l'invio della richiesta.

``` py
# category conditions form field
TICKET_CONDITIONS_FIELD_ID = 'condizioni_field_id'
TICKET_CONDITIONS_TEXT = _('Dichiara altresì di aver letto '
                            'e compreso quanto scritto sopra '
                            'e di assumere ogni responsabilità '
                            'su quanto di seguito dichiarato')
```

### Riepilogo dati dell'utente ad apertura richiesta

Definisce la formattazione e la visibilità dell'intestazione (heading) della richiesta. Questi parametri permettono di mostrare dinamicamente i dati del soggetto richiedente o di chi compila la richiesta (es. in caso di delega), utilizzando placeholder per il nome utente e il codice fiscale.

``` py
# new ticket heading text (user informations)
SHOW_HEADING_TEXT = True
TICKET_HEADING_TEXT = _('Soggetto richiedente: <b>{user}</b>'
                        '<br><span class="x-small">[{taxpayer}]</span>')
TICKET_COMPILED_HEADING_TEXT = getattr(
    settings,
    "TICKET_COMPILED_HEADING_TEXT",
    _("Compilato da: <b>{user}</b>" '<br><span class="x-small">[{taxpayer}]</span>'),
)
```

### Stati di chiusura

Definisce la mappatura degli esiti finali di una richiesta. Ogni tupla associa un valore numerico a una descrizione testuale, permettendo di categorizzare il successo o il fallimento della risoluzione per fini statistici e di reportistica.

``` py
CLOSING_LEVELS = getattr(
    settings,
    "CLOSING_LEVELS",
    (
        (-1, _("Rifiutata")),
        (0, _("Non risolta")),
        (1, _("Risolta con successo")),
        (2, _("Non definita")),
    ),
)
```

### Livelli di priorità

Configurazione della scala di urgenza applicabile alle richieste. I livelli permettono agli operatori di ordinare il proprio carico di lavoro in base alla criticità dell'istanza pervenuta.

``` py
PRIORITY_LEVELS = (
    ('-2',_('Molto alta')),
    ('-1',_('Alta')),
    ('0',_('Normale')),
    ('1',_('Bassa')),
    ('2',_('Molto bassa')),
)
```

### Limite richieste giornaliere

Soglia di sicurezza per prevenire l'abuso del sistema o l'intasamento degli uffici da parte di singoli utenti. L'impostazione del valore a 0 rimuove ogni restrizione, consentendo l'invio illimitato di richieste.

``` py
# 0 = unlimited
MAX_DAILY_TICKET_PER_USER = 10
```

### Statistiche

Parametri per il modulo di reportistica. Consentono di limitare l'intervallo temporale delle statistiche mostrate in dashboard (es. ultimi 30 giorni) e di decidere se mostrare o meno il dettaglio delle richieste per singolo utente.

``` py
STATS_SHOW_TICKETS_BY_USER = False
STATS_MAX_DAYS = 30
```

### Alert

Messaggi di avviso dinamici utilizzati per informare l'operatore o l'utente su variazioni di stato critiche, come la perdita di competenza su una pratica o errori di accesso in sola lettura dovuti alla condivisione delle richieste.

``` py
# ticket competence abandoned
NO_MORE_COMPETENCE_OVER_TICKET = getattr(
    settings, "NO_MORE_COMPETENCE_OVER_TICKET", _("Nessuna competenza sulla richiesta")
)

# ticket operator readonly access
READONLY_COMPETENCE_OVER_TICKET = getattr(
    settings,
    "READONLY_COMPETENCE_OVER_TICKET",
    _("Hai accesso alla richiesta in sola lettura"),
)

# ticket user readlonly access
TICKET_SHARING_USER_ERROR_MESSAGE = getattr(
    settings,
    "TICKET_SHARING_USER_ERROR_MESSAGE",
    _(
        "Impossibile effettuare l'operazione."
        "<br>"
        "Nonostante tu abbia precompilato la richiesta, "
        "è l'utente <b>{}</b> che l'ha sottomessa"
    ),
)
```

### Testi email

Personalizzazione completa dei template per la comunicazione via email. È possibile modificare gli header e i footer istituzionali, nonché i messaggi di notifica per ogni evento del ciclo di vita della richiesta (creazione, aggiornamento, assegnazione a operatore, chiusura task).  
Supporta l'inserimento dinamico di variabili come ticket_id, url e hostname.

``` py
# E-mail messages
MSG_HEADER = getattr(
    settings,
    "MSG_HEADER",
    _(
        """Gentile utente,
questo messaggio è stato inviato da {hostname}.
Per favore non rispondere a questa email.

-------------------

"""
    ),
)

MSG_FOOTER = getattr(
    settings,
    "MSG_FOOTER",
    _(
        """

-------------------

Per problemi tecnici contatta il nostro staff.
Cordiali saluti.
"""
    ),
)

UNAVAILABLE_TICKET_CATEGORY = getattr(
    settings,
    "UNAVAILABLE_TICKET_CATEGORY",
    _("""La tipologia di richiesta non è attiva"""),
)

NEW_TICKET_CREATED_ALERT = getattr(
    settings, "NEW_TICKET_CREATED_ALERT", _("""Richiesta "{}" creata con successo""")
)

NEW_TICKET_CREATED = getattr(
    settings,
    "NEW_TICKET_CREATED",
    _(
        """{added_text}

L'identificativo univoco di questa transazione è {ticket}.

Clicca qui {url} per prenderne visione."""
    ),
)

TICKET_UPDATED = getattr(
    settings,
    "TICKET_UPDATED",
    _(
        """La richiesta "{ticket}" è stata aggiornata con il seguente messaggio:

{message}"""
    ),
)

USER_TICKET_MESSAGE = getattr(
    settings,
    "USER_TICKET_MESSAGE",
    _(
        """Hai {status} un nuovo messaggio per la richiesta \"{ticket}\"

Clicca qui {url} per aprire il pannello dei messaggi."""
    ),
)

TICKET_DELETED = getattr(
    settings,
    "TICKET_DELETED",
    _("""La richiesta "{ticket}" è stata eliminata correttamente."""),
)

SUMMARY_USER_EMAIL = getattr(
    settings,
    "SUMMARY_USER_EMAIL",
    _(
        """La seguente richiesta {event msg}:

{ticket}"""
    ),
)

SUMMARY_EMPLOYEE_EMAIL = getattr(
    settings,
    "SUMMARY_EMPLOYEE_EMAIL",
    _(
        """Ci sono {opened_ticket_number} richieste da gestire.

{tickets_per_office}"""
    ),
)

NEW_TICKET_CREATED_EMPLOYEE_BODY = getattr(
    settings,
    "NEW_TICKET_CREATED_EMPLOYEE_BODY",
    _(
        """E' stata effettuata una nuova richiesta all'ufficio {destination_office}.

Utente: {ticket_user}
Oggetto: {ticket_subject}
Descrizione: {ticket_description}

URL: {ticket_url}"""
    ),
)

NEW_TICKET_SHARED_EMPLOYEE_BODY = getattr(
    settings,
    "NEW_TICKET_SHARED_EMPLOYEE_BODY",
    _(
        """E' stata trasferita la competenza di una richiesta all'ufficio {destination_office}.

Utente: {ticket_user}
Oggetto: {ticket_subject}
Descrizione: {ticket_description}

URL: {ticket_url}"""
    ),
)

TASK_CLOSED_EMPLOYEE_NOTIFY_BODY = getattr(
    settings,
    "TASK_CLOSED_EMPLOYEE_NOTIFY_BODY",
    _(
        """Messaggio agli operatori dell'ufficio {office}.
Il task {task} della richiesta {ticket} è stata chiusa.

URL: {ticket_url}"""
    ),
)

TASK_OPEN_EMPLOYEE_NOTIFY_BODY = getattr(
    settings,
    "TASK_OPEN_EMPLOYEE_NOTIFY_BODY",
    _(
        """Messaggio agli operatori dell'ufficio {office}.
E' stato creato un nuovo task ({task}) per la richiesta {ticket}.

URL: {ticket_url}"""
    ),
)

NEW_MESSAGE_RECEIVED_EMPLOYEE_BODY = getattr(
    settings,
    "NEW_MESSAGE_RECEIVED_EMPLOYEE_BODY",
    _(
        """Hai ricevuto un nuovo messaggio per la richiesta \"{ticket}\"

Clicca qui {url} per aprire il pannello dei messaggi."""
    ),
)

NEW_TICKET_ASSIGNED_TO_OPERATOR_BODY = getattr(
    settings,
    "NEW_TICKET_ASSIGNED_TO_OPERATOR_BODY",
    _(
        """Ti è stata assegnata una nuova richiesta da {manager}.

Utente: {ticket_user}
Oggetto: {ticket_subject}
Descrizione: {ticket_description}

URL: {ticket_url}"""
    ),
)
```