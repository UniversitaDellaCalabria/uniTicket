# Uffici

Gli Uffici rappresentano le unità operative minime di uniTicket. Sono micro-aree con una specifica sfera di competenza, afferenti a una Struttura, a cui vengono assegnati gli utenti con il ruolo di Operatori.

L'ufficio è il cuore pulsante della gestione: ogni ufficio può gestire più tipologie di richieste (o nessuna, se l'ufficio ha funzioni puramente di coordinamento).  

Gli operatori assegnati a un ufficio specifico avranno i permessi necessari per visualizzare, prendere in carico e lavorare esclusivamente sulle richieste di loro competenza.

### Stati

L'amministratore può gestire la visibilità operativa di un ufficio tramite il suo stato:

* **Attivo**: l'ufficio è pienamente operativo e visibile ai manager durante la fase di gestione e assegnazione delle competenze.

* **Non attivo**: l'ufficio viene nascosto nelle fasi di gestione delle competenze, utile per uffici stagionali o in fase di dismissione, senza doverne eliminare i dati storici.

### Ufficio predefinito della struttura

Ogni volta che viene creata una Struttura, il sistema genera automaticamente un ufficio "speciale" di coordinamento, denominato di default "Help-Desk".

Gli operatori afferenti a questo ufficio hanno la facoltà di visualizzare e gestire tutte le richieste dell'intera struttura di appartenenza.

!!! warning "Attenzione"
    A causa del suo ruolo centrale nell'architettura dei permessi della struttura, l'ufficio predefinito non può essere eliminato né reso inattivo. È il punto di garanzia che assicura che nessuna richiesta rimanga mai senza un potenziale gestore.

### Uffici ad uso interno

Se un ufficio è marcato come "ad uso interno" potrà ricevere richieste solo da altri uffici della sua struttura.