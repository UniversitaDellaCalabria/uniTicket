.. django-form-builder documentation master file, created by
   sphinx-quickstart on Tue Jul  2 08:50:49 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Template Bootstrap Italia (linee guida AGID)
============================================

| La libreria Bootstrap Italia è il modo più semplice e sicuro per costruire interfacce web moderne, inclusive e semplici da mantenere.
| Completamente open-source, costruita sulle fondamenta di **Bootstrap 4.3.1**, di cui eredita tutte le funzionalità, componenti, griglie e classi di utilità, personalizzandole secondo le Linee Guida di Design per i siti web della Pubblica Amministrazione, Bootstrap Italia usa i pattern e i componenti definiti nello UI Kit di Designers Italia e li trasforma in codice già pronto all'uso!

https://github.com/italia/design-django-theme

Gestione allegati firmati digitalmente
======================================

Grazie all’integrazione della libreria Django Dynamic Form e di FileSig, la piattaforma è in grado di gestire file PDF firmati digitalmente e P7M e di effettuare una validazione delle firme, visualizzandone i dettagli.

.. thumbnail:: images/signed_attachments.png

Il Django Form Field utilizzato per questa feature è stato basato su:
https://github.com/peppelinux/FileSignatureValidator

Costruzione dinamica dei form
=============================

App *django-form-builder* integrata

https://github.com/UniversitaDellaCalabria/django-form-builder

Gestione Javascript di Django Formsets
======================================

Implementazione javascript del controllo frontend per la gestione di campi di input “complessi”, costruiti da field elementari e pertanto adattabili alle più disparate esigenze di configurazione dei moduli di input.

https://docs.djangoproject.com/en/2.2/topics/forms/formsets/

JQuery Datatables
=================

Gestione ottimizzata dei record delle tabelle, che velocizza il caricamento delle pagine e non sovraccarica il server e il client in fase di renderizzazione dei risultati di una ricerca.

https://datatables.net/
https://github.com/peppelinux/django-datatables-ajax

Single Sign On (SAML2)
=====================

Federare uniTicket in un systema SSO SAML2 è una operazione estremamente semplice.
All'interno dei requirements già otteniamo le dipendenze a ``djangosaml2`` e ``pysaml2``.
Per federare uniTicket presso un IdP basterà ereditare la configurazione presso ``saml2_sp/settings.py`` e
modificarla a proprio piacimento.

Nello specifico i parametri rilevanti sono:

- entityid;
- required_attributes;
- metadata['remote'];

Modificare questi ultimi ed eventuali altri sulla base dei parametri tecnici per la federazione alla organizzazione di propria appartenenza.
Per attivare la configurazione scelta basterà includere in ``settingslocal.py`` una dichiarazione di questo genere:

.. code-block:: python

    if 'saml2_sp' in INSTALLED_APPS:
        from saml2_sp.settings import *
