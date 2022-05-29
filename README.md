![Build status](https://travis-ci.org/UniversitaDellaCalabria/uniTicket.svg?branch=master)
![Python version](https://img.shields.io/badge/license-Apache%202-blue.svg)
![Codecov](https://codecov.io/gh/UniversitadellaCalabria/uniTicket/branch/master/graph/badge.svg)
![License](https://img.shields.io/badge/python-3.7%20%7C%203.8%20%7C%203.9-blue.svg)


uniTicket
---------

Django **Unified Ticket System** è un sistema software di ticketing ed helpdesk per il tracciamento e la digitalizzazione dei flussi di richieste e documentali.

Principali caratteristiche:

- Multi Tenant. Un unico sistema a supporto di diversi uffici e aree organizzative;
- Possibilità di trasferire e condividere ticket tra differenti uffici/aree;
- Possibilità di aggiungere clausole di consenso da accettare prima di aprire un ticket;
- Interdipendenza tra ticket;
- Lista di attività atomiche per ogni ticket, per guidare l’utente nel processo di lavorazione ed evasione;
- Form builder, possibilità di creare i moduli di inserimento per ogni categoria di ticket;
- Campi di input personalzzati, campi complessi e Django Formsets configurabili tramite widget;
- Gestione allegati firmati digitalmente (PDF e P7M), con controllo e validazione dell’integrità dei dati;
- Chat e videoconferenza per operatori e utenti;
- Report di riepilogo via email che include la lista dei ticket pendenti agli operatori;
- JQuery Datatables integrato, per una gestione Ajax con processamento lato server dei dati, per ottime performance;
- Template grafico Bootstrap Italia (Linee Guida di Design pe la P.A.) reponsive per una esperienza di navigazione ottimale anche sui dispositivi mobili;
- Integazione SAML2 SSO (pySAML2);

[Documentazione ufficiale](https://uniticket.readthedocs.io/it/latest/index.html) su **readthedocs** per installazione e utilizzo del software.


Dump example data
-----------------
````
./manage.py dumpdata -e auth -e contenttypes -e sessions --indent 2 -e admin.logentry > ../dumps/example_conf.json
````

Load example data
-----------------

````
./manage.py loaddata dumps/example_conf.json
````

- Manager user (username: user1 / password: secret1!)
- Operator user (username: user2 / password: secret2!)
- Normal user (username: utente / password secret1!)

## Docker

### Docker image

````
docker pull ghcr.io/UniversitaDellaCalabria/uniTicket:latest
````

### Docker compose

Install Docker using the packages distributed from the official website and the following tools.
````
sudo apt install jq
sudo pip install docker-compose
````

Please do your customizations in each _settingslocal.py_ files and/or in the example dumps json file.

We can do that with the following steps:

- Execute `bash docker-prepare.sh`
- Customize the example data and settings contained in `examples-docker/` if needed (not necessary for a quick demo)

Run the stack
````
sudo docker-compose up
````

Configure a proper DNS resolution for trust-anchor.org. In GNU/Linux we can configure it in `/etc/hosts`:
````
127.0.0.1   localhost  trust-anchor.org relying-party.org cie-provider.org
````

Point your web browser to `http://relying-party.org:8001/oidc/rp/landing` and do your first oidc authentication.


## Usage

The demo proposes a small federation composed by the following entities:

 - Federation Authority, acts as trust anchor and onboarding system. It's available at `http://127.0.0.1:8000/`. It has also an embedded Spid provider and a embedded Relying Party available at `/oidc/rp/landing`.
 - OpenID Relying Party, available at `http://127.0.0.1:8001/`
 - CIE OpenID Provider, available at `http://127.0.0.1:8002/`

In the docker example we have only the Federation Authority with an embedded SPID OP and a RP.

Examples Users and Passwords:

 - __admin__ __oidcadmin__
 - __user__ __oidcuser__


Gallery
-------

![Home](gallery/user_dashboard.png)
_**Image 1:** Example of user dashboard_

![Home](gallery/manager_dashboard.png)
_**Image 2:** Example of manager dashboard_


Production Setup
----------------

After the following actions being made, copy and adapt the production configurations that you found in `uwsgi_setup/` folder.

````
apt install python3-dev python3-pip libmagic-dev
pip3 install virtualenv
virtualenv -ppython3 uniticket.env
source uniticket.env/bin/activate
git clone https://github.com/UniversitaDellaCalabria/uniTicket.git uniticket
cd uniticket

# CONFIGURATION
# create your project settings
cat uni_ticket_project/settingslocal.py.example > uni_ticket_project/settingslocal.py

# edit settings ...
# set DEBUG=False

# create your MysqlDB
export USER='thatuser'
export PASS='thatpassword'
export HOST='%'
export DB='uniticket'

# tested on Debian 10
sudo mysql -u root -e "\
CREATE USER IF NOT EXISTS '${USER}'@'${HOST}' IDENTIFIED BY '${PASS}';\
CREATE DATABASE IF NOT EXISTS ${DB} CHARACTER SET = 'utf8' COLLATE = 'utf8_general_ci';\
GRANT ALL PRIVILEGES ON ${DB}.* TO '${USER}'@'${HOST}';"

# that's for saml2 (not mandatory, can even disable djangosaml2 in settings.INSTALLED_APPS)
cat saml2_sp/settings.py.example > saml2_sp/settings.py

# unical base template - modify templates/base-setup.html to customize your UI
curl https://raw.githubusercontent.com/italia/design-django-theme/master/bootstrap_italia_template/templates/bootstrap-italia-base.html --output templates/base-setup.html

# create generic certificates
pushd saml2_sp/saml2_config/certificates
openssl req -nodes -new -x509 -newkey rsa:2048  -days 3650 -keyout key.pem -out cert.pem
popd
# END CONFIGURATION

pip3 install -r requirements.txt
pip3 install uwsgi

sudo apt install mariadb-server libmariadbclient-dev
sudo apt install poppler-utils xmlsec1 gobject-introspection
sudo apt install supervisor

./manage.py migrate
./manage.py compilemessages
./manage.py collectstatic
./manage.py createsuperuser
./manage.py runserver

# if everything works, the big part is done!
````
