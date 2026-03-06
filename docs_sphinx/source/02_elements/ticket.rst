.. django-form-builder documentation master file, created by
   sphinx-quickstart on Tue Jul  2 08:50:49 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Ticket
======

Un ticket è una richiesta aperta, da un utente , per una specifica tipologia. 

.. thumbnail:: images/operator_takes_ticket.png

Stati del ticket
----------------

- **Aperto**

  | Appena creato, il ticket si trova in uno stato pendente. 
  | Non ancora assegnato ad alcun operatore, esso può essere modificato, chiuso o eliminato dall’utente che lo ha creato.

- **Assegnato**

  | Una volta preso in carico dall’operatore competente, il ticket passa a questo stato e può essere gestito per l’evasione della richiesta. 
  | L’utente che lo ha creato non può più apportare modifiche ma può chiuderlo in qualsiasi momento.

- **Chiuso**

  | Se è il ticket è stato chiuso dall’utente prima di essere stato preso in carico da un operatore, esso non può essere riaperto. In caso contrario, un operatore con facoltà di gestione può riaprirlo e apportare ulteriori modifiche.
  | Un ticket può essere chiuso solo quando gli eventuali ticket da cui dipende e le eventuali attività collegate, tutti elementi vincolanti, sono stati chiusi.

Priorità
--------

- **Molto alta**
- **Alta**
- **Normale** (priorità di default alla creazione del ticket)
- **Bassa**
- **Molto bassa**

