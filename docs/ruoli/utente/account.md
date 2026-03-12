# Account

La sezione Account è lo spazio dedicato alla gestione del profilo utente e alla verifica dei dati sincronizzati dai sistemi di autenticazione dell'ente. In questa area, l'utente può controllare la propria identità digitale e personalizzare le modalità di interazione con la piattaforma.

### Gestione del Profilo

Il profilo raccoglie le informazioni anagrafiche e di carriera che determinano i permessi di accesso alle diverse categorie di richieste:

* **Dati anagrafici**: visualizzazione di nome, cognome e codice fiscale (solitamente non modificabili se provenienti da SPID/SAML2);

* **Identificativi di carriera**: visualizzazione della matricola studente o del codice dipendente;

* **Email di contatto**: indirizzo predefinito per la ricezione di tutte le notifiche di sistema (solitamente modificabile).

!!! info "Informazione"
    I campi modificabili sono definiti in [EDITABLE_FIELDS](../../setup/configurazione/parametri-avanzati.md#modifica-profilo-utente) (uniticket/accounts/settings.py) e personalizzabili definendo la variabile nel settingslocal.py.