# File settingslocal.py

E' il punto di ingresso per tutte le configurazioni variabili e sensibili e non deve mai essere tracciato su Git (è incluso nel .gitignore) poiché contiene credenziali e parametri specifici del server ospitante.

### Scopo del file

Mentre il file *settings.py* principale definisce l'ossatura del progetto e le impostazioni di default, il *settingslocal.py *permette di:

* **Proteggere i dati sensibili**: chiavi di crittografia, password del database e segreti SAML2.

* **Adattare l'istanza**: definire l'URL del sito, i contatti dell'assistenza e il nome della struttura.

* **Configurare le integrazioni**: attivare o disattivare plugin come LDAP, AppIO o Titulus.

### Creazione del settingslocal.py

```
cd uni_ticket_project
# copy and modify as your needs
cp settingslocal.py.example settingslocal.py
```