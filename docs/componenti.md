# Componenti

### Template Bootstrap Italia

Rappresenta lo standard di riferimento per la creazione di interfacce web moderne, inclusive e conformi ai requisiti di accessibilità. Completamente open-source e basata su Bootstrap 5.2.3, la libreria eredita la solidità del framework originale (griglie, componenti e utility) declinandola secondo le Linee Guida di Design per la Pubblica Amministrazione. Grazie all'integrazione dei pattern definiti nello UI Kit di Designers Italia, permette di trasformare i requisiti di design in codice pronto all’uso, garantendo un'esperienza utente coerente e professionale.

[https://italia.github.io/bootstrap-italia/](https://italia.github.io/bootstrap-italia/)  
[https://github.com/italia/design-django-theme](https://github.com/italia/design-django-theme)

### Costruzione dinamica dei form

Il sistema integra l'applicazione django-form-builder, uno strumento avanzato che consente la generazione dinamica di moduli di inserimento e la definizione di campi personalizzati direttamente dall'interfaccia amministrativa. Questa soluzione permette di adattare rapidamente i flussi di raccolta dati alle specifiche esigenze di ogni ufficio o procedimento, senza richiedere interventi diretti sul codice sorgente.

[https://github.com/UniversitaDellaCalabria/django-form-builder](https://github.com/UniversitaDellaCalabria/django-form-builder)

### Gestione allegati firmati digitalmente

Grazie alla sinergia tra Django Dynamic Form e la libreria FileSignatureValidator, uniTicket offre un supporto nativo per la gestione di documenti con valore legale. La piattaforma è in grado di elaborare file in formato PDF e P7M (CAdES) firmati digitalmente, eseguendo automaticamente la validazione delle firme e rendendone disponibili i dettagli tecnici. Il campo di input specializzato garantisce che solo i file correttamente firmati e integri vengano accettati dal sistema.

[https://github.com/peppelinux/FileSignatureValidator](https://github.com/peppelinux/FileSignatureValidator)

### Gestione Javascript di Django Formsets

Per la gestione di set di dati complessi e ripetitivi, il sistema adotta un'implementazione JavaScript avanzata dei Django Formsets. Questa tecnologia permette di manipolare lato frontend gruppi di campi correlati (aggiunta o rimozione dinamica di righe), offrendo la flessibilità necessaria per configurare moduli di input articolati che si adattano dinamicamente alle scelte dell'utente durante la compilazione.

[https://docs.djangoproject.com/en/5.2/topics/forms/formsets/](https://docs.djangoproject.com/en/5.2/topics/forms/formsets/)

### JQuery Datatables

L'interazione con grandi moli di dati è ottimizzata tramite l'integrazione di JQuery Datatables. Grazie al processamento asincrono (Ajax) lato server, la visualizzazione dei record è fluida e reattiva: il sistema carica solo le informazioni necessarie alla vista corrente, riducendo drasticamente i tempi di rendering e il carico computazionale sia sul server che sul browser dell'utente, anche in presenza di migliaia di richieste.

[https://datatables.net/](https://datatables.net/)  
[https://github.com/peppelinux/django-datatables-ajax](https://github.com/peppelinux/django-datatables-ajax)

### Editor Markdown Avanzato

Integrazione di django-markdownx per consentire la redazione di contenuti testuali in formato Markdown con anteprima in tempo reale. Questa libreria facilita la scrittura di testi formattati, garantendo la generazione di codice HTML sicuro e conforme.

* **Anteprima Live**: visualizzazione immediata del risultato finale durante la digitazione.

* **Gestione Immagini**: supporto al drag-and-drop per l'upload di immagini con ridimensionamento automatico.

* **Integrazione Django Admin**: estensione semplice dei campi TextField sia nei form pubblici che nell'interfaccia di amministrazione.

[https://github.com/neutronX/django-markdownx](https://github.com/neutronX/django-markdownx)

### Generazione Documentale (WeasyPrint)

Per la generazione di documenti PDF di alta qualità, uniTicket utilizza WeasyPrint, un motore di rendering visuale che trasforma pagine HTML e fogli di stile CSS in file PDF conformi agli standard.

A differenza di altri generatori basati su motori meno recenti, WeasyPrint garantisce:

* **Fedeltà Grafica**: supporto avanzato per i fogli di stile CSS3, permettendo di mantenere la coerenza visiva con il design system di Bootstrap Italia anche nei documenti esportati.

* **Documentazione dinamica**: Generazione automatica di ricevute di sottomissione, riepiloghi dei richieste e report amministrativi basati sui dati inseriti in tempo reale.

* **Standard Web**: utilizzo di tecnologie web standard per la definizione del layout, facilitando la personalizzazione dei template di stampa senza strumenti proprietari.

[https://weasyprint.org/](https://weasyprint.org/)
[https://github.com/Kozea/WeasyPrint](https://github.com/Kozea/WeasyPrint)