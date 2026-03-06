# Run

## Debug

    ./manage.py runserver

## Produzione

Ricorda di eseguire compilemessages per attuare la localizzazione e compilescss/collectstatic per compilare e copiare tutti i file statici nelle cartelle di produzione:

    ./manage.py compilemessages
    ./manage.py compilescss
    ./manage.py collectstatic

!!! tip "Suggerimento"
    Per un ulteriore controllo in fase di debug è possibile utilizzare i comandi seguenti con uwsgi:

    /etc/init.d/uni_ticket stop

    uwsgi --ini /opt/uni_ticket/uwsgi_setup/uwsgi.ini.debug