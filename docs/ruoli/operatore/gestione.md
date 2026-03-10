# Gestione delle richieste

Una volta arriva una nuova istanza, questa appare nella coda dell'ufficio competente. L'Operatore ha il compito di guidare la richiesta attraverso diverse fasi operative utilizzando gli strumenti messi a disposizione dal sistema.

### Presa in carico

Prima di poter operare su una richiesta, l'Operatore deve dichiararne la gestione. L'azione assegna formalmente la richiesta all'Operatore (che ne diventa il gestore o "owner"). Da questo momento, lo stato passa da "Aperta" ad "Assegnata", notificando l'avvio della lavorazione all'utente.

### Strumenti di Istruttoria

Una volta acquisita la gestione, l'interfaccia abilita una serie di funzioni specifiche per l'elaborazione della pratica:

* **Note**: permette di inserire annotazioni interne visibili solo agli altri operatori dell'ufficio:
    * utilità: annotare passaggi tecnici, dubbi o promemoria che non devono essere comunicati all'utilizzatore.

* **Messaggi**: costituisce il canale di comunicazione ufficiale con l'utente:
    * utilità: inviare risposte formali, richiedere chiarimenti o sollecitare l'invio di ulteriore documentazione.

* **Aggiungi attività**: consente di creare dei sotto-task operativi all'interno della richiesta:
    * utilità: delegare una parte del lavoro a un collega o tracciare passaggi intermedi obbligatori (es: "Verifica condizioni fattibilità").

### Gestione della Competenza

Il sistema permette di gestire scenari in cui la richiesta deve essere spostata o condivisa:

* **Trasferisci competenza:** sposta la richiesta verso un altro ufficio o una diversa struttura:
    * **utilità**: quando l'utente ha sbagliato destinatario (trasferimento )o quando la pratica richiede l'intervento di un ufficio specialistico differente (condivisione).

* **Abbandona competenza**: rilascia la gestione della richiesta senza chiuderla:
    * **utilità**: utile in caso di competenza condivisa e mansioni terminate.

### Relazioni tra pratiche

* **Aggiungi dipendenza**: permette di collegare la richiesta corrente a un'altra già presente nel sistema:
    * **utilità**: indicare che la risoluzione di una pratica è vincolata all'esito di un'altra (relazione "padre-figlio" o correlazione per argomento).

### Conclusione del ciclo di vita

L'obiettivo finale del flusso è la risoluzione. L'Operatore procede alla chiusura selezionando l'esito più appropriato:

* **Successo**: l'istanza è stata evasa positivamente;

* **Rifiuto/Non risolta/Non definita**: l'istanza non è stata accolta o non è gestibile.

!!! info "Nota operativa"
    tutte le azioni compiute dall'Operatore (cambi di stato, messaggi, trasferimenti) vengono registrate in un log cronologico non modificabile, garantendo la piena tracciabilità dell'operato dell'ufficio.