# Autenticazione SAML2

Federare uniTicket in un sistema SSO (Single Sign-On) basato su protocollo SAML2 è un'operazione estremamente lineare. Grazie all'architettura modulare, l'applicativo include già nei propri requisiti le librerie djangosaml2 e pysaml2, standard di riferimento per l'integrazione di Django con i Service Provider SAML2.

Per federare uniTicket presso un Identity Provider (IdP), come ad esempio sistemi SPID o CIE, è sufficiente configurare il modulo dedicato ereditando i parametri presenti in saml2_sp/settings.py e adattandoli alle specifiche tecniche della propria infrastruttura.

### Parametri di configurazione

I parametri fondamentali su cui agire all'interno del file di configurazione sono:

* **entityid**: l'identificativo univoco del Service Provider (solitamente l'URL del metadato dell'istanza).

* **required_attributes**: la lista degli attributi utente necessari per il login (es. codice fiscale, email, nome).

* **metadata["remote"]**: l'URL o il path locale dei metadati XML forniti dall'Identity Provider.

È possibile modificare questi e altri parametri avanzati (come i certificati X.509) sulla base dei requisiti tecnici della federazione della propria organizzazione.

### Attivazione del modulo

Per rendere operativa l'autenticazione tramite SAML2, è necessario includere le applicazioni djangosaml2 e saml2_sp all'interno della lista INSTALLED_APPS nel proprio settingslocal.py:

``` python
INSTALLED_APPS = [
     ...

    ## SAML2 SP
    'djangosaml2',
    'saml2_sp',
]
```

### Inizializzazione del file di impostazioni

Prima di procedere con la personalizzazione, creare il file di configurazione partendo dall'esempio fornito nel repository:

```
# Bash
cd saml2_sp
cp settings.py.example settings.py
```