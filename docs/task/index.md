# Attività (Task)

Le attività sono componenti granulari che consentono una gestione strutturata del workflow.  
Una singola richiesta può contenere una o più attività, ognuna con il proprio ciclo di vita e responsabile.

### Anatomia di un'Attività

Ogni attività è caratterizzata da elementi specifici che ne definiscono l'operatività:

* **Oggetto**: titolo sintetico dell'azione da compiere (es. "Verifica conformità allegato A");

* **Descrizione**: dettaglio approfondito delle operazioni richieste all'operatore;

* **Stato**: indicazione del progresso (es. "Aperta", "Assegnata", "Chiusa");

* **Visibilità**: specifica se l'attività debba essere visibile all'utente che ha aperto la richiesta.

### Creazione di un'attività

Le attività possono essere aggiunte "a caldo" ad ogni richiesta o associate alla tipologia in modo da essere automaticamente ereditate 
da ogni istanza.

### Livelli di accesso

Tutti gli operatori coinvolti nella gestione della richiesta hanno facoltà di agire sulle attività, non esistono vincoli legati agli uffici di afferenza.

### Proprietà e Vincoli Logici

Le attività non sono semplici promemoria, ma possono influenzare direttamente il flusso del ticket padre:

* **Vincolo di chiusura**: se attivata, impedisce la chiusura del ticket principale finché l'attività non risulta completata;

* **Priorità**: livello di urgenza specifico dell'attività, che può differire da quello del ticket principale;

### Tipologie di Interazione

Il sistema gestisce la visibilità e l'interazione in base al ruolo dell'utente:

* **Visualizzazione Utente**: il richiedente può vedere l'avanzamento delle attività (se reso pubblico) per monitorare lo stato della propria pratica;

* **Gestione Operatore**: l'operatore può aggiornare lo stato, aggiungere note interne o allegare documenti specifici per quel singolo compito;