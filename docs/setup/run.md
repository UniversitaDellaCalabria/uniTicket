# Run

### Creazione delle tabelle

Dopo aver creato il database vuoto, è necessario istruire Django affinché generi tutte le tabelle, gli indici e le relazioni necessarie al funzionamento dei vari moduli (ticket, account, organizzazione, ecc.). Questo processo viene gestito tramite il sistema delle migrazioni.

```
# Bash
./manage.py migrate
```

### Creazione del Superuser

Per poter accedere al pannello di amministrazione e iniziare a configurare gli uffici e le aree organizzative, è necessario creare almeno un account con privilegi massimi. Il comando richiederà l'inserimento di un nome utente, un indirizzo email e una password.

```
# Bash
./manage.py createsuperuser
```

Una volta completata la migrazione del database e la creazione dell'amministratore, è possibile avviare uniTicket. La modalità di esecuzione varia a seconda che ci si trovi in un ambiente di sviluppo o in un server di produzione.

### Debug (Ambiente di Sviluppo)

Per le fasi di sviluppo, test locale o debug, è possibile utilizzare il server web integrato di Django. Questo strumento include il hot-reloading, ovvero riavvia automaticamente il processo a ogni modifica del codice sorgente.

```
# Bash
./manage.py runserver
```

### Produzione

In un ambiente di produzione, il server deve essere ottimizzato per le prestazioni e la sicurezza. Prima di avviare l'applicativo tramite un server WSGI (come Gunicorn o uWSGI), è obbligatorio eseguire le operazioni di compilazione e raccolta degli asset:

* Localizzazione: generazione dei file binari (.mo) per le traduzioni.

* Asset Statici: raccolta di tutti i file CSS, JavaScript e immagini nella cartella di pubblicazione definita in STATIC_ROOT.

```
# Bash
./manage.py compilemessages
./manage.py collectstatic

```
!!! tip "Suggerimento"
    Per un ulteriore controllo in fase di debug, specialmente per diagnosticare problemi relativi alla configurazione del server web o ai permessi dei file, è possibile arrestare il servizio di sistema e avviare manualmente uwsgi in modalità interattiva:

    ```
    # Bash
    /etc/init.d/uni_ticket stop
    uwsgi --ini /opt/uni_ticket/uwsgi_setup/uwsgi.ini.debug
    ```