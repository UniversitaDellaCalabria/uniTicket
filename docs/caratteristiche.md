# Principali caratteristiche

### Architettura e Flussi Organizzativi

* **Multi-tenant nativo**: il sistema consente la coesistenza di più uffici o [aree organizzative](aree-organizzative/strutture.md) indipendenti (es. Risorse Umane, IT, Segreteria Didattica) all'interno di un'unica installazione. Ogni tenant mantiene la propria autonomia configurativa, i propri operatori e i propri database di richeste, garantendo isolamento dei dati e scalabilità.

* **Trasferimento e Condivisione Inter-ufficio**: supera la compartimentazione stagnante permettendo di smistare una richiesta verso un altro [ufficio](aree-organizzative/uffici.md) competente o di condividerne la visibilità. Questo assicura che l'utente non debba mai riaprire una pratica se ha sbagliato destinatario, migliorando la collaborazione interna.

* **Interdipendenza tra Richieste**: consente di legare la risoluzione di una richiesta principale (Parent) alla chiusura di uno o più richieste secondarie (Child) aperti verso altri uffici. È la funzione chiave per gestire processi complessi che richiedono il "nulla osta" di diversi dipartimenti.

### Gestione Intelligente dei Dati (Form Builder)

* **Dynamic Form Builder**: un'interfaccia visuale permette agli amministratori di creare moduli di inserimento ad hoc per ogni categoria. Non ci si limita a semplici campi di testo: è possibile definire la struttura dati esatta necessaria per quella specifica pratica.

* **Input Complessi e Django Formsets**: supporta la gestione di set di dati ripetitivi (es. l'inserimento di più figli a carico o più titoli di studio) tramite widget avanzati. Grazie ai Formsets, l'interfaccia rimane pulita pur permettendo l'invio di strutture dati nidificate e complesse.

* **Clausole di Consenso e Compliance**: è possibile configurare termini di servizio, informative privacy (GDPR) o dichiarazioni di responsabilità, senza il
cui esplitico consenso la richiesta non può essere sottomessa.

### Sicurezza e Validazione Documentale

* **Gestione Firma Digitale (PDF e P7M)**: uniTicket non è un semplice contenitore di file. Include un motore di validazione che verifica l'integrità e la validità dei certificati di firma digitale. Questo permette di dematerializzare completamente procedimenti che richiedono valore legale (es. contratti, istanze formali).

* **Integrazione SSO**: supporto nativo per l'autenticazione tramite Identity Provider istituzionali (come SPID, CIE o sistemi universitari) basati su protocolli come SAML2 e OATH2. Garantisce un accesso sicuro, unificato e il provisioning automatico dei profili utente.

### Strumenti per l'Operatore (Back-office)

* **Workflow guidato tramite Attività**: ogni tipologia di richiesta può avere una lista di controllo (checklist) definita. Le attività guidano l'operatore attraverso i passaggi obbligatori necessari per l'evasione, riducendo l'errore umano e garantendo l'omogeneità del servizio.

* **Performance con Ajax e Datatables**: anche con milioni di record, la gestione rimane fluida. L'integrazione di jQuery Datatables con processamento lato server (Server-side) permette ricerche, filtri e ordinamenti istantanei senza appesantire il browser dell'operatore.

* **Reportistica e Notifiche**: statistiche dedicate per il monitoraggio del volume di richieste in determinate fasce orarie e dei tempi di riposta dei singoli uffici.

### Comunicazione e User Experience

* **Collaborazione in Real-time**: include un pannello di messaggistica dedicato per ciascuna richiesta, tramite il quale utente ed operatori possono comunicare, e un sistema di chat real-time per comunicazioni atomiche. 

* **Design System P.A. (Bootstrap Italia)**: l'interfaccia segue rigorosamente le Linee Guida di Design per i servizi web della Pubblica Amministrazione. Questo garantisce non solo un'estetica moderna, ma soprattutto un'accessibilità certificata e una navigazione ottimizzata per i dispositivi mobili.

* **Supporto Markdown**: il sistema integra la formattazione dei testi tramite Markdown, permettendo a operatori e utenti di inviare risposte chiare e ben strutturate. È possibile inserire facilmente grassetti, elenchi puntati, link ipertestuali e snippet di codice, migliorando drasticamente la leggibilità delle istruzioni tecniche o amministrative.

### Ecosistema e Integrazioni Istituzionali

* **Integrazione AppIO**: consente l'invio di notifiche push direttamente sullo smartphone del cittadino tramite l'app IO, informandolo tempestivamente sullo stato di avanzamento della sua pratica.

* **Protocollo Titulus (Cineca)**: integrazione nativa per la protocollazione automatica dei flussi in entrata e in uscita. Ogni richiesta può essere trasformata in un documento protocollato a norma di legge all'interno del sistema documentale dell'ente.