# Richieste (Ticket)

Rappresentano l'unità fondamentale di interazione nel sistema: sono istanze formali aperte da un utente per una specifica tipologia (categoria) di servizio o supporto.

### Stati della richiesta

Il ciclo di vita di una richiesta è regolato da stati precisi che ne determinano i permessi di modifica e le possibilità d'azione per le parti coinvolte:

* **Aperta**: è lo stato iniziale post-creazione. La richiesta si trova in una fase "pendente" e non è ancora stato assegnata a un operatore. In questa fase, l'utente creatore ha il massimo controllo: può modificarne il contenuto, chiuderlo o eliminarlo definitivamente.

* **Assegnata**: la richiesta passa in questo stato non appena viene presa in carico dall'operatore competente (o assegnata a lui da un Manager). Da questo momento, l'operatore può gestire l'evasione della richiesta. Per garantire l'integrità del processo, l'utente non può più modificare i dati inseriti, ma conserva la facoltà di chiudere la richiesta se ritiene che la richiesta non sia più necessaria.

* **Chiusa**: rappresenta la conclusione del flusso di lavorazione.

!!! info "Tag chiusura"
    All'operazione di chiusura è sempre associata una motivazione e, se questa viene effettuata da un operatore e non dall'utente che ha aperto la richiesta, dei tag:

    * **Chiusa con successo**: la richiesta è stata evasa correttamente e il problema è stato risolto o il servizio erogato;
    
    * **Rifiutata****: la richiesta è stata valutata come non ammissibile (es. mancanza di requisiti formali o invio di documentazione errata);
    
    * **Non risolta**: la richiesta è stata gestita ma, per cause esterne o impedimenti tecnici, non è stato possibile arrivare a una soluzione definitiva;
    
    * **Non definita**: la richiesta è stata considerata non gestibile dall'ufficio (es. ticket inviato per errore, contenuto incomprensibile o spam).

Se la richiesta viene chiusa dopo l'assegnazione, un operatore con i permessi necessari può procedere alla sua riapertura per ulteriori integrazioni.

!!! warning "Vincoli di chiusura"
    Una richiesta non può essere chiusa se esistono vincoli attivi. Devono essere preventivamente chiusi tutte le richieste da cui questa dipende (dipendenze gerarchiche) e tutte le attività collegate (task), qualora siano stati impostati come elementi vincolanti.

### Priorità

La priorità permette agli uffici di organizzare la coda di lavoro in base all'urgenza della richiesta. Ogni richiesta viene creata con una priorità predefinita, che può essere successivamente variata dagli operatori o dai manager.

* Molto alta
* Alta
* Normale (default)
* Bassa
* Molto bassa