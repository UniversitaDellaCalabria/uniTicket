# Messaggi

La sezione Messaggi è lo strumento di comunicazione asincrona integrato in uniTicket. A differenza di una comune email, ogni messaggio inviato o ricevuto attraverso questa funzione è indissolubilmente legato a una richiesta specifica, garantendo la piena tracciabilità di quanto dichiarato dalle parti durante l'intero ciclo di vita della richiesta.

### Funzionalità principali
L'interfaccia dei messaggi è progettata per essere semplice e immediata, simile a una conversazione di messaggistica moderna, ma con rigore documentale.

1. **Cronologia della Conversazione**  
All'interno di ogni conversazione, l'utente può visualizzare l'elenco cronologico di tutti gli scambi:

* **Messaggi dell'Utente**: identificati chiaramente come inviati dal richiedente.
    
* **Risposte dell'Operatore**: messaggi provenienti dall'ufficio competente. Il sistema può mostrare il nome dell'operatore o una dicitura generica dell'ufficio a seconda delle impostazioni di privacy dell'ente.

2. **Invio di Integrazioni**  
Se un operatore richiede ulteriori informazioni, l'utente può rispondere direttamente dalla sezione messaggi.  

È possibile:
    
* Inserire testo formattato in markdown.
    
* Allegare nuovi documenti (seguendo i vincoli di formato e dimensione definiti in PERMITTED_UPLOAD_FILETYPE e MAX_UPLOAD_SIZE).

### Notifiche e Badge

Per evitare che l'utente debba controllare costantemente il portale, uniTicket implementa un sistema di alert multi-livello:

* **Badge sulla Dashboard**: un indicatore numerico rosso sui pulsanti "Messaggi" segnala il numero di comunicazioni non ancora lette.

* **Email di Avviso**: ogni volta che un operatore invia un messaggio, il sistema genera un'email automatica (basata sul template USER_TICKET_MESSAGE) che contiene un link diretto per accedere alla conversazione.