.. uniTicket documentation master file, created by
   sphinx-quickstart on Tue Jul  2 08:50:49 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

uniTicket - Documentazione
==========================

Django **Unified Ticket System (uniTicket)** è un sistema software di ticketing 
ed helpdesk per il tracciamento e la digitalizzazione dei flussi di richieste e documentali.

Principali caratteristiche:

- Multi Tenant. Un unico sistema a supporto di diversi uffici e aree organizzative;
- Possibilità di trasferire e condividere ticket tra differenti uffici/aree;
- Possibilità di aggiungere clausole di consenso da accettare prima di aprire un ticket;
- Interdipendenza tra ticket;
- Lista di attività atomiche per ogni ticket, per guidare l'utente nel processo di lavorazione ed evasione;
- Form builder, possibilità di creare i moduli di inserimento per ogni categoria di ticket;
- Campi di input personalzzati, campi complessi e Django Formsets configurabili tramite widget;
- Gestione allegati firmati digitalmente (PDF e P7M), con controllo e validazione dell'integrità dei dati;
- Report di riepilogo via email che include la lista dei ticket pendenti agli operatori;
- JQuery Datatables integrato, per una gestione Ajax con processamento lato server dei dati, per ottime performance;
- Template grafico reponsive per una esperienza di navigazione ottimale anche sui dispositivi mobili;
- Integazione SAML2 SSO (pySAML2);
- Pienamente rispondente alle linee guida AGID per le interfacce grafiche.

**Github:** https://github.com/UniversitaDellaCalabria/uniTicket

---------------------------------------

.. toctree::
   :maxdepth: 2
   :caption: Installazione e Setup

   Requisiti <01_getting-started/getting_started.rst>

.. toctree::
   :maxdepth: 2
   :caption: Ticket, Categorie e Attività

   Ticket <02_elements/ticket.rst>
   Categorie <02_elements/categories.rst>
   Attività <02_elements/task.rst>

.. toctree::
   :maxdepth: 2
   :caption: Aree Organizzative

   Strutture <03_organizational-areas/organizational_areas.rst>

.. toctree::
   :maxdepth: 2
   :caption: Tipologie utenti

   Manager <04_usertypes/usertypes.rst>

.. toctree::
   :maxdepth: 2
   :caption: Gestione Ticket (Management)

   Ticket <05_management/management.rst>

.. toctree::
   :maxdepth: 2
   :caption: Manager

   Dashboard <06_manager/dashboard.rst>
   Categorie <06_manager/categories.rst>
   Uffici <06_manager/offices.rst>

.. toctree::
   :maxdepth: 2
   :caption: Operatore

   Dashboard <07_operator/dashboard.rst>

.. toctree::
   :maxdepth: 2
   :caption: Utente utilizzatore

   Dashboard <08_user/dashboard.rst>
   Ticket <08_user/ticket.rst>

.. toctree::
   :maxdepth: 2
   :caption: Operazioni comuni a tutti gli utenti

   Messaggi <09_common-operations/common_operations.rst>

.. toctree::
   :maxdepth: 2
   :caption: Caratteristiche del sistema

   Template Bootstrap Italia <10_features/features.rst>












