# Inizializzazione del Database e del Sistema

Una volta completata la configurazione del file settingslocal.py, è necessario preparare l'ambiente del database e generare la struttura delle tabelle. Di seguito sono riportati i passaggi per la configurazione su MariaDB e la creazione dell'utenza amministrativa.

### Creazione dello Schema (Esempio per MariaDB)

Il seguente script automatizza la creazione dell'utente di sistema e del database dedicato. È fondamentale che il set di caratteri sia impostato su utf8 con collation utf8_general_ci per garantire la corretta memorizzazione di simboli e accenti.

!!! info "Nota"
    L'host '%' permette la connessione da qualsiasi indirizzo IP; per una maggiore sicurezza in produzione, si consiglia di limitarlo a 'localhost' o all'IP specifico del server applicativo.

```
# Bash
# Definizione delle variabili d'ambiente per la configurazione
export USER='that-user'
export PASS='that-password'
export HOST='%'
export DB='uniticket'

# Esecuzione dei comandi SQL (testato su Debian 10/11/12 con MariaDB)
sudo mysql -u root -e "\
CREATE USER IF NOT EXISTS '${USER}'@'${HOST}' IDENTIFIED BY '${PASS}';\
CREATE DATABASE IF NOT EXISTS ${DB} CHARACTER SET = 'utf8' COLLATE = 'utf8_general_ci';\
GRANT ALL PRIVILEGES ON ${DB}.* TO '${USER}'@'${HOST}';"
```