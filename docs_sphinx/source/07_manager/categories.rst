.. django-form-builder documentation master file, created by
   sphinx-quickstart on Tue Jul  2 08:50:49 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Tipologie di richieste
======================

Aggiungi nuova
--------------

| La creazione di una nuova tipologia di richiesta prevede l’inserimento dei campi Nome e Descrizione, la scelta dei ruoli di accessibilità per l’apertura di nuove richieste, del tipo di richiesta e della possibilità di mostrare all'utente una intestazione con i suoi dati personali in fase di apertura di un nuovo ticket.
| Una tipologia appena creata si presenta con stato *Non attiva*, perché sprovvista di un modulo di input attivo e di un ufficio attivo competente.

.. thumbnail:: images/category_new.png

Dettaglio, modifica e competenza ufficio
----------------------------------------

| La schermata di dettaglio, oltre alle informazioni della tipologia, presenta l’elenco dei moduli di input a essa associati e le relative clausole obbligatorie di accettazione.
| Da questa sezione è possibile anche aggiornare l’ufficio competente, scegliendo dall’elenco di quelli attivi afferenti alla struttura.

.. thumbnail:: images/category_detail.png

Moduli di input
---------------

| Per essere visibile e attiva, una tipologia di richiesta deve avere, oltre a un ufficio competente, un modulo di input attivo.

.. thumbnail:: images/category_input_modules.png

| Agli utenti manager è consentita la creazione di innumerevoli moduli per ogni tipologia, ma sempre uno sarà quello attivo.
| Non è possibile eliminare moduli di input tramite i quali sono stati già creati dei ticket. Ogni ticket, infatti, è collegato a un preciso modulo e il suo workflow sarà operativo anche se il modulo dovesse essere disabilitato.

La costruzione di un modulo di input prevede la scelta e l’inserimento di singoli campi, selezionabili dall’elenco disponibile.

.. thumbnail:: images/category_input_module_detail.png

L’utente può visualizzare in qualsiasi momento l’anteprima del modulo, anche in fase di costruzione, così da rendersi conto di quello che la piattaforma presenterà all’utente all’atto della creazione di un nuovo ticket.

Clausole di accettazione
------------------------

| L’inserimento delle :ref:`clausole` è indipendente dal modulo utilizzato e si applica ai ticket creati per la tipologia in questione.
| Una clausola può essere creata/modificata/disattivata/eliminata dal manager facilmente.

.. thumbnail:: images/category_condition.png

