# Tipologie di richieste

Una tipologia di richiesta rappresenta l’ambito del ticket che viene aperto.
Ogni tipologia è associata a un ufficio, che ha la competenza della gestione delle richieste in arrivo.

## Stati
Attiva: visibile agli utenti in fase di creazione del ticket  
Non attiva: non visibile agli utenti

## Livelli di visibilità

Ogni tipologia prevede 3 livelli di visibilità che consentono l’apertura di ticket a

* personale dell’organizzazione
* utenti dell’organizzazione
* ospiti
* utenti anonimi (la compilazione del form non richiede il login)

## Ticket accessibili a utenti anonimi

Questa opzione consente agli utenti non loggati di accedere direttamente all’URL del form per l’apertura di un nuovo ticket.  
Il form, in questo caso, sarà provviso di un codice CAPTCHA per evitare abusi.

## Tipo di richiesta “Notifica“

Se selezionata, questa opzione permetterà agli utenti di creare dei ticket che non seguono il normale flusso di gestione. Una richiesta di tipo notifica verrà chiuso automaticamente dal sistema, immediatamente dopo la sua apertura, e verrà assegnato, in modalità random, a uno degli operatori dell’ufficio competente (se assenti, a un manager/operatore help-desk della struttura). 

!!! tip "Suggerimento"
    Casi d’uso: richieste di partecipazione ad eventi, semplici notifiche da parte degli utenti.

## Moduli di input

Per essere attiva e visibile, una categoria deve prevedere un modulo di input attivo, che guiderà l’utente nell’apertura del ticket mediante compilazione dei campi ad esso collegati, e un ufficio collegato attivo, che avrà la competenza di gestirne le richieste.

## Clausole di accettazione obbligatorie

Semplici condizioni che, se attive, l’utente è costretto ad accettare in fase di creazione di un ticket per la tipologia in questione.

## Attività predefinite (task)

Attività elementari che, se attive, saranno assegnate automaticamente a ogni ticket creato e ne condizioneranno la chiusura.