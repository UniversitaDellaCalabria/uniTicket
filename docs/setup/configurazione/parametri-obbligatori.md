# Configurazione Parametri Obbligatori

Di seguito sono elencati i parametri che devono essere necessariamente valorizzati nel *settingslocal.py* per garantire il corretto funzionamento di uniTicket.

### Chiave segreta di Django

La stringa alfanumerica univoca utilizzata da Django come "seme" (seed) per tutte le sue operazioni crittografiche. È il pilastro che garantisce l'integrità dei dati scambiati tra il server e l'utente, come la firma dei cookie di sessione e la generazione dei token CSRF. 

!!! warning "Attenzione"
    Per motivi di sicurezza, non deve mai essere condivisa o pubblicata in repository pubblici.

``` py
SECRET_KEY = 'la-tua-chiave-segreta-molto-lunga'
```

**Generazione nuova key**  

È possibile generare una chiave sicura e casuale direttamente da terminale utilizzando l'utility nativa di Django:

```
python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

### Path URL admin

Definisce il percorso personalizzato per accedere all'interfaccia di amministrazione. Cambiare questo valore rispetto al default 'admin/' aggiunge un ulteriore livello di protezione (security through obscurity) contro i tentativi di attacco automatizzati.

``` py
ADMIN_PATH = 'gestione-riservata'
```

### Nome dell'host

Il parametro HOSTNAME definisce il dominio principale dell'istanza, mentre ALLOWED_HOSTS è una misura di sicurezza che impedisce attacchi di tipo HTTP Host Header. In produzione, deve contenere solo il nome a dominio associato al server.

!!! info "Nota"
    In fase di test o sviluppo in locale è possibile utilizzare '*' per non essere vincolati.

``` py
HOSTNAME = 'ticket.mia-org.it'
ALLOWED_HOSTS = [HOSTNAME]
```

### Database

Configurazione della connessione al database relazionale. uniTicket è ottimizzato per MariaDB e MySQL, ma supporta altri motori compatibili con Django (come PostgreSQL). 

!!! warning "Attenzione"
    La direttiva STRICT_TRANS_TABLES è fondamentale per garantire l'integrità dei dati forzando il database a segnalare errori in caso di inserimento di dati non validi.

``` py
# esempio MariaDB / MySQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'nome_db',
        'HOST': 'localhost',
        'USER': 'utente_db',
        'PASSWORD': 'password_sicura',
        'PORT': '',
        'OPTIONS': {'init_command': "SET sql_mode='STRICT_TRANS_TABLES'"}
    },
}
```

### SMTP

Parametri necessari per l'invio delle notifiche automatiche (notifiche di cambio stato, messaggi agli utenti, alert di sistema). È fondamentale assicurarsi che il server SMTP consenta l'invio dall'indirizzo specificato.

``` py
DEFAULT_FROM_EMAIL = 'uniticket.noreply@mia-org.it'
SERVER_EMAIL = 'uniticket.server@mia-org.it'
EMAIL_HOST = 'smtp.mia-org.it'
EMAIL_HOST_USER = 'user'
EMAIL_HOST_PASSWORD = 'password'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_SENDER = 'uniticket@mia-org.it'
```

### Lista degli amministratori per notifiche eccezioni

Elenco dei responsabili tecnici che riceveranno via email i dettagli degli errori critici (Exception) generati dal sistema. 

!!! info "Nota"
    Django invierà il report tecnico (traceback) solo se il parametro DEBUG è impostato su False.

``` py
ADMINS = [('Responsabile IT', 'admin@mia-org.it'),]
```

### Criptazione URL token

uniTicket utilizza la specifica JWE (JSON Web Encryption) per proteggere i dati sensibili veicolati all'interno degli URL (come i token di attivazione o di accesso rapido). È necessario generare una coppia di chiavi RSA e fornire il percorso assoluto della chiave privata.

``` py
# UNITICKET JWE support
UNITICKET_JWE_RSA_KEY_PATH = '/path/to/your/private_key.pem'
# end JWE support
```

### Captcha

Parametri per la gestione della sicurezza dei moduli pubblici. La chiave (CAPTCHA_SECRET) e il sale (CAPTCHA_SALT) servono a crittografare la soluzione del test visivo per prevenire sottomissioni automatizzate da parte di bot.

``` py
# CAPTCHA encryption
CAPTCHA_SECRET = b'cambiami-con-stringa-casuale'
CAPTCHA_SALT = b'cambiami-con-un-sale-casuale'
CAPTCHA_EXPIRATION_TIME = 45000 # espresso in millisecondi
CAPTCHA_DEFAULT_LANG = 'it'
# end CAPTCHA encryption
```