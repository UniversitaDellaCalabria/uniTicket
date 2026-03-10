# Operatore

L'area dedicata all'Operatore rappresenta il cuore gestionale di uniTicket. Questo spazio è progettato per fornire agli addetti agli [uffici](/aree-organizzative/uffici/) tutti gli strumenti necessari per prendere in carico, lavorare e risolvere le richieste pervenute, garantendo un flusso di lavoro ordinato e tracciabile.

L'Operatore non si limita a rispondere ai messaggi, ma agisce come il gestore del ciclo di vita della richiesta all'interno della propria sfera di competenza.

Attraverso questa sezione, l'Operatore può:

* **Gestire il carico di lavoro**: visualizzare e prendere in carico le richieste afferenti al proprio ufficio o assegnate dai manager;

* **Elaborare le istanze**: interagire con i dati inseriti dagli utenti, validare allegati e avanzare lo stato di lavorazione;

* **Collaborare in team**: utilizzare note interne e attività (task) per coordinarsi con i colleghi della stessa struttura;

* **Risolvere e classificare**: chiudere le richieste fornendo un riscontro formale e associando l'esito corretto per fini statistici.

### Lo Switch di Profilo (Multitenancy)

In uniTicket, l'identità dell'utente è unica, ma le sue funzioni possono cambiare. Un utente con privilegi amministrativi non atterra direttamente nella sezione gestionale, ma mantiene la possibilità di agire come un utente comune.

Per passare alla gestione operativa delle richieste, l'utente deve effettuare un cambio di contesto manuale: nell'header, in alto a destra, è presente un pulsante "Ruolo", che consente di cambiare contesto in base ai ruoli ricoperti nelle varie strutture;

In alternativa a ciò, è possibile utilizzare direttamente gli URL di accesso alle varie risorse. uniTicket non memorizza il cambio di profilo in sessione ma utilizza [appositi path](/setup/configurazione/parametri-avanzati/#url-path-ruoli) per accedere alle singole risorse, effettuando dei check sui permessi (es: /operator/struttura/risorsa-da-gestire/).

### Ambiti di Competenza e Permessi

In uniTicket, l'operatività di un utente è rigorosamente delimitata dalla sua affiliazione a uno o più Uffici. A differenza dell'utilizzatore, i cui permessi dipendono dagli attributi del profilo, l'Operatore agisce in base alle deleghe ricevute dai manager delle strutture.

Il sistema garantisce la riservatezza e l'ordine operativo attraverso due pilastri:

* **Specializzazione per Categoria**: l'Operatore visualizza esclusivamente le richieste appartenenti alle categorie di competenza degli uffici a cui è assegnato;

* **Segregazione dei dati**: i contenuti delle richieste gestite da un ufficio (es. Area Risorse Umane) non sono accessibili agli operatori di altri uffici (es. Area Tecnica), a meno di espliciti trasferimenti della pratica.

### Gerarchia Operativa e Visibilità

La capacità di azione dell'Operatore è definita dal ruolo assegnato all'interno della struttura:

* **Operatore di Ufficio**: l'utente standard incaricato della gestione quotidiana:
    * **Accesso**: visualizza le richieste del proprio ufficio e può prenderle in carico per diventarne il gestore primario.

* **Operatore Ufficio Predefinito (Help-Desk)**: una figura con privilegi trasversali all'interno della struttura:
    * **Accesso**: può visualizzare e intervenire su tutte le richieste della struttura, indipendentemente dall'ufficio specifico di destinazione;
    * **Funzione**: agisce spesso come primo livello di supporto o come smistatore verso uffici più specialistici.

!!! warning "Attenzione"
    La competenza sulle richieste è sempre degli uffici, mai dei singoli operatori. Questo significa che tutti gli utenti afferenti a un ufficio con competenze di gestione su una richiesta possono agire su quest'ultima. Questo comportamento garantisce resilienza a periodi di assenze prolungate degli addetti ai lavori e delega all'organizzazione della struttura la definizione di regole per l'evasione delle pratiche.