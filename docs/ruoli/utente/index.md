# Utente semplice

L'area dedicata all'Utente Utilizzatore rappresenta l'interfaccia principale per l'interazione con l'organizzazione. Questo spazio è progettato per centralizzare l'invio di istanze, segnalazioni o richieste di supporto, garantendo la massima trasparenza sull'intero ciclo di vita di ogni pratica.

Attraverso questa sezione, l'utente può:

* **Sottoporre richieste**: accedere al catalogo dei servizi messi a disposizione dalle diverse Strutture dell'ente;

* **Monitorare l'iter**: verificare in tempo reale lo stato di avanzamento e le fasi di lavorazione delle proprie richieste;

* **Comunicare con l'ente**: interagire direttamente con gli operatori competenti tramite messaggistica interna e chat;

* **Personalizzare l'esperienza**: gestire il proprio profilo utente e configurare le preferenze per la ricezione delle notifiche.

### Profilazione e Accesso Condizionale

In uniTicket, la visibilità delle tipologie di richieste non è uguale per tutti. Il sistema adotta un meccanismo di controllo dinamico basato sugli attributi del profilo utente per mostrare esclusivamente i servizi pertinenti al ruolo del richiedente. Questo approccio garantisce che processi riservati (come i rimborsi missioni per i dipendenti) non siano accessibili a utenti esterni o non autorizzati.

#### I Livelli di Differenziazione

Il sistema classifica l'utente in tre macro-categorie operative, determinate dalle configurazioni d'ambiente (settingslocal.py):

* **Dipendente (Employee)**: utente identificato dalla presenza di un codice specifico (parametro [EMPLOYEE_ATTRIBUTE_NAME](/setup/configurazione/parametri-avanzati/#utenti-employee-e-internal-user), ad esempio la matricola dipendente):

    * **Accesso**: visualizza tutte le tipologie di richieste riservate al personale interno dell'ente.

* **Utente Interno (es. Studente)**: utente identificato da un attributo di carriera (parametro [USER_ATTRIBUTE_NAME](/setup/configurazione/parametri-avanzati/#utenti-employee-e-internal-user), ad esempio la matricola studente):

    * **Accesso**: abilita la visione dei servizi core (iscrizioni, certificati, tasse) che richiedono uno status di appartenenza attiva all'organizzazione.

* **Utente Ospite (Guest**): utente autenticato (tramite SPID, CIE o registrazione diretta) che non presenta attributi di carriera o dipendenza:

    * **Accesso**: può visualizzare e sottoporre esclusivamente le richieste definite come "Pubbliche" o "Accessibili a tutti".