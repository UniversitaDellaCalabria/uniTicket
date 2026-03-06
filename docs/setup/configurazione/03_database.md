# Database

## Creazione schema

Dopo aver effettuato la configurazione

    # create your MysqlDB
    export USER='that-user'
    export PASS='that-password'
    export HOST='%'
    export DB='uniticket'

    # tested on Debian 10
    sudo mysql -u root -e "\
    CREATE USER IF NOT EXISTS '${USER}'@'${HOST}' IDENTIFIED BY '${PASS}';\
    CREATE DATABASE IF NOT EXISTS ${DB} CHARACTER SET = 'utf8' COLLATE = 'utf8_general_ci';\
    GRANT ALL PRIVILEGES ON ${DB}.* TO '${USER}'@'${HOST}';"
    ## 

## Creazione tabelle

    ./manage.py migrate

## Creazione superuser

    ./manage.py createsuperuser