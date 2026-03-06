# Migrazione da v1 a v2

!!! info "Informazione"
    Questa semplice guida consente di aggiornare agevolmente una istanza di uniTicket v1.x alla versione 2.

## 01 - Stoppare il servizio

    /etc/init.d/uni_ticket stop

## 02 - Export dei ContentType

E' necessario ricostruire la tabella dei ContentType, generata automaticamente da Django all’applicazione delle migrazioni, per mantenere la consistenza delle FK utilizzate dai log.

    # CLI Django
    from django.contrib.contenttypes.models import ContentType
    ct = ContentType.objects.all()

    # old_conf sarà quindi una lista di dizionari
    old_conf = []
    for cct in ct:
    old_conf.append({'pk': cct.pk,
                        'app_label': cct.app_label,
                        'model': cct.model})
    print(old_conf)

Copiare old_conf su un file di testo, ci servirà dopo

## 02 - DB Backup

    # CLI Django
    ./manage.py dumpdata --exclude auth.permission --exclude contenttypes --exclude sessions --indent 2 > path_to_your_file.json

## 03 - Path del progetto

Rinominare la folder del progetto [path]/uniticket in [path]/uniticket_tmp

Creare [path]/uniticket (è preferibile che si usi l’utente linux proprietario di [path]/uniticket)

## 04 - Download repository

    # In [path]/uniticket
    git clone https://github.com/UniversitaDellaCalabria/uniTicket.git

## 05 - Django settings

    cp [path]/uniticket/uniticket/uni_ticket_project/settingslocal.py.example [path]/uniticket/uniticket/uni_ticket_project/settingslocal.py

Modificare le variabili opprtune (ignorare la parte dedicata al DB momentaneamente)

## 06 - Media e statics

Copiare uniticket/data/media e uniticket/data/statics in uniticket/data.

## 07 - Database

Se si intende utilizzare lo stesso DB, eliminare tutte le tabelle presenti altrimenti utilizzare un nuovo DB (opzione consigliata)

Aggiornare i dati relativi nel settingslocal.py

## 08 - Migrazioni

    # CLI Django
    ./manage.py migrate

## 09 - Ripristino dei ContentType

!!! warning "Attenzione"
    Poichè i log dei ticket sono collegati ai ContentType, è necessario sovrascrivere i valori creati da Django nella migrazione iniziale per la consistenza del backup da importare.

Nel seguente script bisogna copiare il contenuto di old_conf stampato al punto 02 - Export dei ContentType

    # CLI Django

    # in una variabile "old_conf" copiare la lista prodotta allo step 01
    old_conf = ...

    from django.contrib.contenttypes.models import ContentType

    ct = ContentType.objects.all()

    # cancella ContentType da aggiornare (quelli presenti nella lista)
    to_delete = []
    for cct in ct:
        app_label = cct.app_label
        model = cct.model
        for old_ct in old_conf:
            if old_ct['app_label'] == app_label and old_ct['model'] == model:
                to_delete.append(cct.pk)
                break
    ct.filter(pk__in=to_delete).delete()

    # aggiorna la pk dei ContentType rimasti
    # per evitare che questa vada in conflitto con il successivo step di importazione
    ct = ContentType.objects.all()
    to_delete = []
    for cct in ct:
        app_label = cct.app_label
        model = cct.model
        # nuova pk che non vada in conflitto con quelle da importare
        pk = cct.pk + 100
        # cambio il valore dei campi del contenttype di origine
        # con dei valori fake per permettere la creazione di uno nuovo
        cct.app_label = pk
        cct.model = pk
        cct.save()
        to_delete.append(cct.pk)
        # crea nuovo ContentType
        ContentType.objects.create(pk=pk, app_label=app_label, model=model)
    ct.filter(pk__in=to_delete).delete()

    # ripristina i contenttypes provenienti dal db di origine (lista old_conf)
    for old_ct in old_conf:
        ContentType.objects.create(pk=old_ct['pk'],
                                app_label=old_ct['app_label'],
                                model=old_ct['model'])

## 10 - Load Data

Sostituire nel dump json le seguenti definizioni con nano (https://it.stealthsettings.com/find-replace-nano-linux-os-x-terminal-text-editor.html)

matricola_dipendente => identificativo_dipendente

matricola_studente => identificativo_utente

Se nel dump sono presenti le tabelle delle app chat e channels abilitarle nelle INSTALLED_APPS del settingslocal e applicare le eventuali migrazioni

    # CLI Django

    ./manage.py loaddata path_to_your_file.json

## 11 - Campo ticket.assigned_data

!!! info "Attenzione"
    Questo campo è presente e viene salvato automaticamente nella nuova release quando un ticket viene preso in carico la prima volta. 

Deve essere inizializzato per tutti i ticket con la data della prima presa in carico. Questo è necessairio solo nel processo di migrazione dalla v1.x alla v2 x.  

    # CLI Django

    from uni_ticket.models import Ticket, TicketAssignment

    tickets = Ticket.objects.filter(assigned_date__isnull=True)

    for ticket in tickets:
        first_taken = TicketAssignment.objects\
                                    .filter(ticket=ticket,
                                            taken_date__isnull=False)\
                                    .values_list("taken_date", flat=True)\
                                    .first()
        if first_taken:
            ticket.assigned_date = first_taken
            ticket.save()
            print("Assigned data update for ticket ", ticket.code)

## 12 - Fine

Se non ci sono criticità è possibile rimuovere la cartella [path]/uniticket_tmp