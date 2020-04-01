.. django-form-builder documentation master file, created by
   sphinx-quickstart on Tue Jul  2 08:50:49 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Ticket
======

La gestione del workflow di un ticket prevede strumenti utilizzabili sia dagli utenti **Manager** che dagli **Operatori**.

Presa in carico e impostazione priorità
---------------------------------------

| La prima operazione da effettuare per la gestione di un ticket è la presa in carico, ovvero l’assunzione della responsabilità di gestione.
| All’atto di questo aggiornamento di stato, all’utente operatore viene chiesto di scegliere il livello di priorità da assegnare al ticket, in modo da posizionarlo correttamente nella lista dei ticket aperti.

.. thumbnail:: images/priority.png

| Un utente manager può, in questa fase, assegnare il ticket a un operatore dell'ufficio competente.

Dettaglio ticket
----------------

| La schermata di dettaglio fornisce tutte le informazioni necessarie, oltre a un set di strumenti di gestione.
| Oltre alla scheda dettagliata, è presente una lista con tutte le operazioni effettuate sul ticket, accompagnate dalla data e dall’utente responsabile.
| E’ disponibile l’elenco delle attività collegate al ticket e quello dei ticket da cui esso dipende.

Aggiornamento priorità
----------------------

In qualsiasi momento della vita del ticket è possibile aggiornare la sua priorità.

Gestione competenza uffici
--------------------------

E’ possibile condividere la competenza del ticket con altri uffici, per motivi organizzativi e gestionali, o scegliere di trasferirla scegliendo di:

- abbandonare completamente i propri privilegi di gestione del ticket;
- mantenere ancora l'accesso ma in sola lettura.

.. thumbnail:: images/ticket_competence.png

Attività del ticket
-------------------

| L’aggiunta, la gestione e la cancellazione delle attività del ticket può essere effettuata con molta flessibilità finché esso si trova in stato "Assegnato".
| Attività non chiuse impediscono la chiusura del ticket.

.. thumbnail:: images/ticket_task.png

.. thumbnail:: images/ticket_task_detail.png

Dipendenze da altri ticket
--------------------------

| Un operatore può assegnare o rimuovere una dipendenza, scegliendo tra i ticket che sono sotto la sua responsabilità.
| Questo crea un legame forte, come per le attività, che impedisce al ticket in oggetto di essere chiuso finchè tutte le sue dipendenze attive non sono chiuse.

.. thumbnail:: images/ticket_dependence.png

.. thumbnail:: images/ticket_dependence_view.png

