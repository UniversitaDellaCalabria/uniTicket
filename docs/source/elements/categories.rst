.. django-form-builder documentation master file, created by
   sphinx-quickstart on Tue Jul  2 08:50:49 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Categorie
=========

| Una categoria rappresenta l’ambito del ticket che viene aperto. 
| Ogni categoria è associata a un ufficio, che ha la competenza della gestione delle richieste in arrivo. 


Stati
-----

- **Attiva** visibile agli utenti in fase di creazione del ticket
- **Non attiva** non visibile agli utenti

Livelli di visibilità in fase di creazione ticket
-------------------------------------------------

Ogni categoria prevede 3 livelli di visibilità che consentono l’apertura di ticket a

- personale dell’organizzazione
- utenti dell’organizzazione
- ospiti

Moduli di input
---------------
Per essere attiva e visibile, una categoria deve prevedere un modulo di input attivo, 
che guiderà l’utente nell’apertura del ticket mediante compilazione dei campi ad esso collegati.

.. _clausole:

Clausole di accettazione obbligatorie
-------------------------------------
Semplici condizioni che, se attive, l’utente è costretto ad accettare in 
fase di creazione di un ticket per la categoria in questione.




