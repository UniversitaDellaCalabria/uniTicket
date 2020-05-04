.. django-form-builder documentation master file, created by
   sphinx-quickstart on Tue Jul  2 08:50:49 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Manager
=======

| Gestisce i ticket aperti verso qualsiasi ufficio della propria struttura.
| Ha la facoltà di creare/modificare/eliminare categorie e uffici e definire l’afferenza degli operatori verso ognuno di essi.
| Può creare nuovi moduli di input associati alle categorie e definire clausole di accettazione.
| Per ogni ticket, può definire nuove assegnazioni, creare attività e aggiornare lo stato.

| Un utente ha i privilegi di manager se afferisce all':ref:`ufficio_predefinito` ed è presente nella lista di utenti in grado di gestire la struttura *(User Manage Organizational Structure)*.
| **Solo gli amministratori della piattaforma web (che accedono al backend di Django) possono gestire queste liste di utenti e, quindi, creare nuovi manager.**

Operatore
=========

| Gestisce il workflow dei ticket collegati agli uffici a cui afferisce.
| Come il manager, può definire per questi nuove assegnazioni, creare attività e aggiornare lo stato.
| Se assegnato all':ref:`ufficio_predefinito` può gestire tutti i ticket della struttura.
| Non ha alcuna facoltà sull’organizzazione di categorie e uffici.


Utente
======

| Può aprire nuovi ticket e consultarne i dettagli.
| Può modificare o eliminare un ticket prima che questo venga preso in carico e può chiuderlo in qualsiasi momento.
| Durante la “vita” del ticket, può interagire con gli operatori mediante il pannello di messaggistica dedicato.
| Non ha i permessi per l’interazione con le funzionalità gestionali.


