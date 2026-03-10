# Gestione delle tipologie di richieste

La configurazione di una tipologia permette di trasformare un semplice modulo di contatto in un processo amministrativo strutturato. Di seguito l'analisi dettagliata di tutti i campi disponibili per il Manager.

### Dati Identificativi e Contesto

Questi campi definiscono l'identità della richiesta e chi deve gestirla:

* **Denominazione**: il nome ufficiale del servizio (es: SCHEDA-SINTESI-PROGETTO);

* **Descrizione**: testo informativo che spiega all'utente le finalità della richiesta e come compilarla;

* **Ufficio di competenza**: l'unità organizzativa (es: Progettazione) che riceverà le istanze e le lavorerà;

* **URL nuova richiesta**: indirizzi diretti per raggiungere il modulo, utili da inserire in portali istituzionali o comunicazioni mirate (es: FaQ).

### Ciclo di Vita e Disponibilità Temporale

Il Manager può automatizzare l'apertura e la chiusura dei servizi:

* **Stato**: indica se la tipologia è attualmente operativa (Attiva/Non attiva);

* **Attiva dal / fino al**: definisce una finestra temporale certa di disponibilità;

* **Messaggio se non attiva**: il testo mostrato all'utente che tenta di accedere al servizio fuori dai termini previsti.

### Profilazione e Sicurezza (Accessibilità)

Questa sezione stabilisce i criteri per l'identificazione certa del richiedente:

* **Target di utenza**: permessi granulari per Utenti anonimi, Ospiti, Studenti e Dipendenti;

* **Autenticazione SPID/CIE**: restrizione che impone l'accesso esclusivamente tramite identità digitale forte, necessaria per istanze con valore legale;

* **Accessibile solo tramite URL**: se attivo, nasconde la tipologia dal catalogo pubblico;

* **Liste e Utenti specifici**: possibilità di restringere l'invio solo a un elenco puntuale di utenti.

### Regole di Business e Flusso Operativo

Parametri che controllano come il sistema gestisce l'invio e le notifiche:

* **Richieste contemporanee / Numero massimo**: definisce se un utente può inviare più istanze (0 = illimitate) o se è limitato a un unico invio;

* **Richiesta di tipo Notifica**: se attivo, la pratica viene considerata "risolta" immediatamente dal sistema senza intervento manuale;

* **Invia email agli operatori**: notifica istantanea al team dell'ufficio per ogni nuova istanza ricevuta;

* **Protocollo obbligatorio**: invia la registrazione di ogni nuova richiesta al sistema di protocollo dell'ente.

### Output e Messaggistica

Personalizzazione del riscontro fornito all'utente:

* **Messaggio di conferma**: testo mostrato all'invio. L'uso di {} inserisce dinamicamente l'oggetto della richiesta (es: Richiesta "{}" creata con successo);

* **Mostra dati dichiarante**: inserisce automaticamente i dati anagrafici nell'intestazione del modulo;

* **Testo in calce per versione stampabile**: note legali o istruzioni che appaiono solo nel PDF generato dal sistema.

### Oggetti collegati

#### Moduli di inserimento (Form Dinamici)

È il cuore della raccolta dati. Il Manager definisce l'interfaccia che l'utente compilerà. Ogni modulo può contenere una combinazione di campi personalizzati:

* **Tipologie di campo**: campi di testo libero (breve o lungo), selettori di data/ora, menu a tendina (dropdown), pulsanti di scelta singola (radio) o multipla (checkbox);

* **Caricamento file**: possibilità di richiedere documenti allegati, con restrizioni su formato (es. solo PDF o P7M) e dimensione massima;

* **Logica di validazione**: impostazione di campi obbligatori o facoltativi e controlli sul formato (es. verifica formale del Codice Fiscale o della Partita IVA);

* **Ordinamento**: trascinamento dei campi per determinare la sequenza logica di compilazione per l'utente.

#### Clausole obbligatorie (Compliance e Privacy)

Fondamentali per la validità legale dell'istanza. Prima di poter trasmettere la richiesta, l'utente deve interagire con questi elementi:

* **Informative Privacy (GDPR)**: testi legali sul trattamento dei dati personali forniti;

* **Dichiarazioni di responsabilità**: clausole ai sensi del D.P.R. 445/2000 (autocertificazioni) in cui l'utente dichiara la veridicità delle informazioni;

* **Modalità di accettazione**: configurazione di checkbox obbligatori che, se non selezionati, inibiscono l'invio della richiesta;

* **Link esterni**: possibilità di inserire collegamenti a regolamenti o bandi completi pubblicati sul portale istituzionale.

#### Attività predefinite (Automazione del Workflow)

Si tratta di Attività (task) interne che vengono generate automaticamente dal sistema nel momento esatto in cui la richiesta viene creata:

* **Guida operativa**: servono a ricordare agli operatori i passaggi necessari (es. "Verifica regolarità pagamenti", "Controllo validità documento d'identità");

* **Vincoli di chiusura**: è possibile configurare il sistema affinché la richiesta non possa essere chiusa se prima non sono state smarcate tutte le attività obbligatorie;

#### Configurazioni Protocollo Informatico (Interoperabilità)

Questo modulo permette a uniTicket di dialogare con il protocollo dell'ente (es. Titulus o sistemi analoghi):

* **Mappatura AOO e Titolario**: definizione dell'Area Organizzativa Omogenea e della classificazione di archivio corretta per quella tipologia di istanza;

#### Risposte predefinite (Template di Comunicazione)

Uno strumento di efficienza per gli operatori, utile a mantenere un tono istituzionale e uniforme:

* **Libreria di modelli**: creazione di testi standard per le situazioni ricorrenti (es. "Richiesta di integrazione documentale", "Comunicazione di avvio procedimento", "Esito positivo");

* **Variabili dinamiche**: inserimento di placeholder che il sistema compila automaticamente (es. il nome del richiedente o il numero della pratica);

* **Riduzione errori**: evita che ogni operatore scriva testi differenti per la stessa procedura, garantendo coerenza formale nelle comunicazioni verso l'esterno.

#### Servizi App IO (Integrazione Nazionale)

Questo modulo permette di interfacciare la singola tipologia di richiesta con la piattaforma IO, l'app dei servizi pubblici.  
Attraverso questa configurazione, il Manager definisce come e quando l'ente deve inviare aggiornamenti push all'utente:

* **Mappatura del Servizio**: associazione della richiesta a uno specifico "Service ID" registrato sul portale dei pagamenti e dei servizi pubblici (tramite l'integrazione con l'API di IO), precedentemente configurato, per la struttura in questione, dal super-admin nell'interfaccia di backend Django;

* **Comunicazione Push**: alla chiusura della richiesta, l'utente riceve una notifica in tempo reale sul proprio dispositivo mobile, aumentando drasticamente la velocità di lettura rispetto alla tradizionale email;

* **Valore Istituzionale**: l'utilizzo di App IO certifica l'identità dell'ente mittente, aumentando la fiducia dell'utente nella comunicazione ricevuta.