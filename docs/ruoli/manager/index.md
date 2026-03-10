# Manager

L’utente Manager rappresenta il vertice decisionale e configurativo di una [Struttura](/aree-organizzative/strutture/) all'interno di uniTicket.  
Se l’Operatore è la figura che lavora sulla singola istanza, il Manager è colui che progetta l’intero ecosistema in cui le istanze si muovono.

Il suo ruolo combina responsabilità organizzative e configurazione tecnica: egli ha la facoltà di decidere quali uffici debbano esistere, quali persone vi debbano lavorare e, soprattutto, quali servizi (tipologie di richiesta) l'ente debba offrire all'utenza esterna e interna.

### Architettura dei Servizi (Tipologie di Richiesta)

Il Manager è l'unico profilo abilitato alla creazione e alla manutenzione del catalogo dei servizi. Egli definisce:

* **L'identità del servizio**: nome, descrizione e messaggistica di cortesia;

* **Le regole di ingaggio**: chi può inviare la richiesta (utenti, dipendenti, ospiti) e con quale grado di sicurezza (login semplice o SPID/CIE);

* **Il ciclo di vita**: finestre temporali di apertura e chiusura automatica dei moduli;

* **La compliance**: inserimento di clausole legali obbligatorie e informative privacy.

### Organizzazione delle Risorse (Uffici e Operatori)

Il Manager modella la struttura burocratica dell'ente nel mondo digitale:

* **Mappatura degli Uffici**: creazione delle unità organizzative che riceveranno le richieste;

* **Gestione del Personale**: assegnazione dei dipendenti ai rispettivi uffici, definendo chi agisce come operatore semplice e chi come supporto trasversale (Help-Desk);

* **Distribuzione del carico**: associazione tra le tipologie di richiesta e gli uffici competenti, garantendo che ogni istanza arrivi nel posto giusto.

### Standardizzazione e Automazione

Per garantire che il servizio sia efficiente e uniforme, il Manager configura strumenti di supporto per gli operatori:

* **Workflow predefiniti**: impostazione di attività (task) che si generano automaticamente per guidare l'operatore nei passaggi obbligatori;

* **Modulistica dinamica**: creazione di form di inserimento che guidano l'utente nella compilazione, riducendo errori e mancanze documentali;

* **Integrazioni di sistema**: configurazione del protocollo informatico per automatizzare la conservazione documentale a norma di legge.

### Lo Switch di Profilo (Multitenancy)

Come per l'operatore, per passare al profilo da Manager, l'utente deve effettuare un cambio di contesto manuale: nell'header, in alto a destra, è presente un pulsante "Ruolo", che consente di cambiare contesto in base ai ruoli ricoperti nelle varie strutture;

In alternativa a ciò, è possibile utilizzare direttamente gli URL di accesso alle varie risorse. uniTicket non memorizza il cambio di profilo in sessione ma utilizza [appositi path](/setup/configurazione/parametri-avanzati/#url-path-ruoli) per accedere alle singole risorse, effettuando dei check sui permessi (es: /manager/struttura/risorsa-da-gestire/).

### La Doppia Natura Operativa (Lo Switch di Ruolo)

Una caratteristica distintiva del Manager in uniTicket è la sua versatilità. Pur avendo accesso a tutte le funzioni di configurazione, il Manager può trovarsi nella necessità di intervenire direttamente sulla gestione di una richiesta.

* **Visualizzazione Gestionale**: l'interfaccia predefinita dove il Manager agisce sui settaggi della struttura, degli uffici e delle categorie;

* **Un Operatore a tutti gli effetti**: il Manager può anche "indossare i panni" dell'operatore, può prendere in carico richieste, rispondere agli utenti, assegnare task e chiudere pratiche.

### Monitoraggio e Trasparenza

Il Manager funge da garante della qualità del servizio. Grazie alla visione d'insieme sulla Struttura, può monitorare:

* **Evasione delle richieste**: controllo del rapporto tra richieste aperte e chiuse per identificare eventuali ritardi;

* **Performance dei team**: verifica dell'attività dei singoli uffici per ottimizzare la distribuzione del personale;

* **Tracciabilità totale**: accesso ai log di sistema per verificare ogni azione compiuta dagli operatori, garantendo la massima trasparenza amministrativa.

!!! summary "In sintesi"
    il Manager non è solo un utente con più permessi, ma è il responsabile dell'efficienza digitale della Struttura. Senza la sua configurazione, il sistema è un guscio vuoto; con la sua gestione, diventa un motore di semplificazione per l'ente e per il cittadino.