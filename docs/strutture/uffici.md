# Uffici

Micro-aree con una specifica sfera di competenza, afferenti a una struttura, a cui possono essere assegnati utenti operatori.

Ogni ufficio può gestire al più una categoria di ticket (o nessuna) e gli operatori ad esso assegnati saranno nelle condizioni di agire sui ticket appartenenti a quest’ultima.

## Stati

* Attivo: visibile agli operatori in fase di gestione delle competenze
* Non attivo: non visibile agli operatori in fase di gestione delle competenze

## Ufficio predefinito della struttura

A ogni struttura è collegato un ufficio “speciale”, di default “Help-Desk“, che dà la facoltà agli operatori ad esso afferenti di poter gestire tutti i ticket aperti in qualsiasi ufficio della struttura stessa.

!!! warning "Attenzione"
    Questo ufficio non può essere eliminato o reso inattivo.
