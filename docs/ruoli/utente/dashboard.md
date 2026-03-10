# Dashboard

La Dashboard rappresenta il centro di controllo digitale per l'utilizzatore. Progettata per offrire una visione d'insieme immediata, permette di monitorare lo stato delle interazioni con l'ente senza dover navigare tra i singoli menu di sistema.

### Indicatori di Stato (Widget)

Nella parte superiore della pagina, una serie di badge numerici fornisce un riepilogo in tempo reale delle pratiche in corso:

* **Aperte**: richieste sottomesse correttamente e in attesa di essere assegnate a un operatore;

* **Assegnate**: richieste attualmente in fase di lavorazione da parte degli uffici competenti;

* **Chiuse**: archivio storico delle istanze completate o risolte.

### Accesso Intelligente ai Servizi

Il pulsante "Nuova richiesta" attiva un sistema di filtraggio dinamico. Il catalogo dei servizi presentato non è statico, ma si adatta automaticamente all'identità digitale del richiedente:

* **Profilo Dipendente**: il sistema propone i servizi interni e le procedure riservate al personale;

* **Profilo utente affiliato (es: studente)**: vengono mostrati i servizi dedicati agli utenti, non dipendenti, dell'organizzazione;

* **Servizi Pubblici:** le categorie ad accesso libero rimangono sempre visibili a prescindere dalla profilazione specifica.

### Canali di Comunicazione e Supporto

La Dashboard centralizza due diverse modalità di interazione, distinguendo tra il valore legale della documentazione e la rapidità del supporto operativo:

#### Messaggi della Richiesta (Comunicazione Asincrona)

Accessibile tramite il pulsante "Messaggi", questa sezione gestisce il flusso ufficiale delle comunicazioni legate a ogni singola pratica. È lo strumento deputato alla messaggistica formale:

* **Tracciabilità**: ogni scambio è indissolubilmente legato a un ID Richiesta, garantendo la conservazione dello storico nel fascicolo digitale;

* **Gestione notifiche**: un indicatore numerico segnala la presenza di nuove comunicazioni inviate dagli operatori che richiedono attenzione;

* **Integrazioni documentali**: permette all'utilizzatore di caricare file aggiuntivi o scaricare documenti prodotti dall'ufficio durante l'istruttoria.

#### Nuova Chat (Comunicazione Sincrona)

Il pulsante "Nuova Chat" attiva un modulo basato su tecnologia WebSocket (Django Channels), pensato per un dialogo istantaneo e meno formale:

* **Supporto immediato**: ideale per risolvere dubbi veloci sulla compilazione o per richiedere chiarimenti rapidi all'operatore in turno;

* **Presenza operativa**: permette di visualizzare lo stato online degli uffici, assicurando una risposta in tempo reale;

* **Recupero informazioni**: la cronologia degli scambi recenti rimane disponibile (fino al limite definito dal parametro MESSAGES_TO_LOAD), facilitando la consultazione di indicazioni ricevute in precedenza.