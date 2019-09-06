.. django-form-builder documentation master file, created by
   sphinx-quickstart on Tue Jul  2 08:50:49 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Strutture
=========

| Una struttura rappresenta una macro area (logica o fisica) dell’organizzazione presso cui il sistema viene utilizzato.
| Questa gestisce per competenza uno o più uffici secondo un principio di ripartizione delle responsabilità.
| In una Università, ad esempio, una struttura potrebbe essere rappresentata da un Dipartimento (o Facoltà).

**Solo gli amministratori della piattaforma web (che accedono al backend di Django) possono creare/modificare/eliminare le strutture.**


Uffici
======

| Micro-aree con una specifica sfera di competenza, afferenti a una struttura, a cui possono essere assegnati utenti operatori.
| Ogni ufficio può gestire al più una categoria di ticket (o nessuna) e gli operatori ad esso assegnati saranno nelle condizioni di agire sui ticket appartenenti a quest’ultima.

Stati
-----

- **Attivo**: visibile agli operatori in fase di gestione delle competenze
- **Non attivo**: non visibile agli operatori in fase di gestione delle competenze

.. _ufficio_predefinito:

Ufficio predefinito della struttura
-----------------------------------

| A ogni struttura è collegato un ufficio “speciale”, detto Help-Desk, che dà la facoltà agli operatori ad esso afferenti di poter gestire tutti i ticket aperti in qualsiasi ufficio della struttura stessa. 
| Questo ufficio non può essere eliminato o reso inattivo.

