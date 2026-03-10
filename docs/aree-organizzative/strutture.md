# Strutture

In uniTicket, la Struttura non è un semplice contenitore nominale, ma definisce un perimetro decisionale e amministrativo. Sebbene la piattaforma sia unica, ogni struttura opera come se avesse un proprio mini-gestionale dedicato, pur condividendo la base dati globale.

### Ripartizione delle Responsabilità

La Struttura permette di implementare il principio di sussidiarietà: 

* **Isolamento dei Dati**: gli operatori di una Struttura "A" non possono intervenire (o visualizzare, a seconda delle configurazioni) sulle richieste della Struttura "B".

* **Governance Locale**: ogni macro-area può avere i propri Manager di Struttura, figure di alto livello che hanno il compito di configurare gli uffici interni, senza dover gravare sugli amministratori centrali del sistema.

### Sicurezza e Governance (Backend vs Frontend)

È fondamentale distinguere tra la gestione dell'architettura e la gestione del servizio:

* **Il Backend (Django Admin)**: è il "cantiere" riservato agli amministratori tecnici della piattaforma. Solo qui è possibile creare l'entità "Struttura", poiché questa operazione modifica l'architettura logica del database e i permessi di accesso di basso livello.

* **Il Frontend (Pannello Manager)**: una volta che l'amministratore ha creato la Struttura e assegnato un Manager, quest'ultimo opererà esclusivamente dal frontend. Il Manager potrà creare uffici e gestire operatori senza mai accedere alle impostazioni critiche del server.

!!! warning "Attenzione"
    L'eliminazione di una Struttura dal backend è un'operazione distruttiva: comporta la rimozione a cascata di tutti gli uffici e le categorie ad essa collegati. Si consiglia sempre di procedere con estrema cautela.