# Gestione degli uffici

In questa sezione, il Manager definisce l'architettura organizzativa della Struttura. La Gestione degli Uffici permette di mappare l'organigramma reale dell'ente all'interno di uniTicket, distribuendo le responsabilità operative e garantendo che ogni istanza venga indirizzata al team corretto.

### Configurazione dell'Ufficio

Ogni ufficio creato nel sistema possiede attributi specifici che ne definiscono il raggio d'azione:

* **Denominazione**: il nome ufficiale dell'unità (es. Ufficio Reclutamento, Settore Post-Laurea);

* **Stato**: possibilità di attivare o disattivare l'ufficio. Un ufficio disattivato non può ricevere nuove richieste.

* **Ad uso intero**: rende l'ufficio visibile solo all'interno della propria struttura nel caso di trasferimento di richieste.

### Gestione degli Operatori (Membri dell'Ufficio)

Il Manager popola l'ufficio assegnando gli utenti che hanno i permessi per operare.

### Assegnazione delle Competenze

Un ufficio può gestire molteplici Tipologie di richiesta (al contrario, invece, la relazione è binaria).

* **Mappatura Servizi**: il Manager associa una o più categorie di richiesta all'ufficio (es. l'ufficio "Tasse" sarà l'unico a vedere e gestire le richieste di tipo "Rimborso contributi");

* **Esclusività**: una volta associata una tipologia a un ufficio, tutti i messaggi e i dati sensibili di quelle richieste saranno visibili solo ai membri di quell'ufficio (e ai Manager della struttura).