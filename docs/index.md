# Panoramica

Django Unified Ticket System (uniTicket) è un sistema software di ticketing ed helpdesk per il tracciamento e la digitalizzazione dei flussi di richieste e documentali, adatto a qualsiasi contesto organizzativo (PA, enti privati, Atenei, ecc...).

## Principali caratteristiche

* multi tenant, per un unico sistema a supporto di diversi uffici e aree organizzative;
* possibilità di trasferire e condividere ticket tra differenti uffici/aree;
* possibilità di aggiungere clausole di consenso da accettare per poter aprire un ticket;
* interdipendenza tra ticket;
* definizione di task, per guidare gli operatori nel processo di lavorazione ed evasione di un ticket;
* form builder, per creare moduli di inserimento personalizzati;
* input complessi e Django Formsets configurabili tramite widget;
* gestione di allegati firmati digitalmente (PDF e P7M), con controllo e validazione dell’integrità dei dati;
* chat e videoconferenza per operatori e utenti;
* statistiche su numeri e tempi di risposta;
* report di riepilogo via email che include la lista dei ticket pendenti agli operatori;
* jQuery Datatables integrato, per una gestione Ajax con processamento lato server dei dati;
* template grafico Bootstrap Italia (Linee Guida di Design pe la P.A.) per una esperienza di navigazione ottimale anche sui dispositivi mobili;
* integazione SAML2 SSO (pySAML2 + djangosaml2);
* integrazione con AppIO;
* integrazione con protocollo Titulus di Cineca;