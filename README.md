![Python version](https://img.shields.io/badge/license-Apache%202-blue.svg)
![License](https://img.shields.io/badge/python-3.5%20%7C%203.6%20%7C%203.7-blue.svg)


uniTicket
---------

Django **Unified Ticket System** è un sistema software di ticketing ed helpdesk per il tracciamento e la digitalizzazione dei flussi di richieste e documentali.

Principali caratteristiche:

- Multi Tenant. Un unico sistema a supporto di diversi uffici e aree organizzative;
- Possibilità di trasferire e condividere ticket tra differenti uffici/aree;
- Possibilità di aggiungere clausole di consenso da accettare prima di aprire un ticket;
- Interdipendenza tra ticket;
- WebChat (websocket) con possibilità di accedere in videoconferenza con gli operatori della piattaforma (jitsi);
- Lista di attività atomiche per ogni ticket, per guidare l'utente nel processo di lavorazione ed evasione;
- Form builder, possibilità di creare i moduli di inserimento per ogni categoria di ticket;
- Campi di input personalzzati, campi complessi e Django Formsets configurabili tramite widget;
- Gestione allegati firmati digitalmente (PDF e P7M), con controllo e validazione dell'integrità dei dati;
- Report di riepilogo via email che include la lista dei ticket pendenti agli operatori;
- JQuery Datatables integrato, per una gestione Ajax con processamento lato server dei dati, per ottime performance;
- Template grafico reponsive per una esperienza di navigazione ottimale anche sui dispositivi mobili;
- Integazione SAML2 SSO (pySAML2);
- Pienamente rispondente alle linee guida AGID per le interfacce grafiche.

[Documentazione ufficiale](https://uniticket.readthedocs.io/it/latest/index.html) su **readthedocs** per installazione e utilizzo del software.


uniTicket
---------

Django **Unified Ticket System** Is a support software that let us manage tickets and generic submission modules with our user.
Featurset:

- Multi Tenant. Multiple office and organizational areas support in a single, unified, system;
- Possibility to transfer and share tickets between different office/areas;
- Possibility to add data consent or agreement submission before a ticket being created;
- ticket interdependencies;
- todo list for every ticket, to follow user to do things before submission;
- Custom fields, custom complex field, custom multi row (table) fields with configurable fancy widgets;
- Pdf and p7m signed fields, with validation on data integrity (attachment);
- Report summary via email about pending tickets to office's operators;
- datatables ajax server side processing, very good performances on mobile device;
- Responsive template for a better mobile experience;
- SAML2 SSO integration (pySAML2);
- Fully compliant Agid visual guidelines.

Consult the [Official Documentation](https://uniticket.readthedocs.io/it/latest/index.html) at readthedocs for usage specifications and advanced topics.

Gallery
-------

![Home](data/gallery/user_dashboard.png)
_**Image 1:** Example of user dashboard_

![Home](data/gallery/manager_dashboard.png)
_**Image 2:** Example of manager dashboard_

Docker Image
------------

````
# please do not use standard distribution package
# apt install docker docker.io docker-compose

# use official docker repositories instead
apt-get install docker-ce docker-ce-cli containerd.io

cd uniTicket

# build the containers and run them
# sudo docker-compose up

# build without composer
docker image build --tag uniticket:v1 .

# Run on localhost:8000
docker run -t -i -p 8000:8000 --name uniticket uniticket:v1
````

Docker Container
----------------

````
docker ps

# get state and id of containers
docker container ls

# get a terminal into a running container
docker container exec -it b075a1193428 /bin/bash

# list changed file in the container
docker container diff b075a1193428
# install and mofiy things with apt/vi ...
# commit changes in a new image (don't do this is you haven't yet created a registry, see next chapter)
docker container commit ab7e1c57b31a uniticket:v1.2

# backup and restore an image
docker save uniticket:v1.2 -o uniticket.v1.2.docker.img
docker image load -i uniticket.v1.2.docker.img

# resource live statistics about a container
docker container stats b075a1193428

# inspect container environemnt
docker container inspect b075a1193428

# display running processes in the container
docker container top b075a1193428
````

Docker Swarm
------------
Single node Docker swarm [health check WiP]

````
# create the swam
docker swarm init

# create a registry is swarm is composed by more then one node ...
# exec registry as an app on localhost
docker run -d -p 5000:5000 --restart=always --name registry registry:2
# tag a local docker image by its uid in the registry
docker tag 46c4806e5d61 localhost:5000/uniticket
# upload it
docker push localhost:5000/uniticket

# create a service
docker service create --name="uniticket" --publish 8000:8000/tcp --replicas 2 localhost:5000/uniticket

# see status
docker service ps uniticket --no-trunc

# see wich network (gateway) is associated to the service
docker network ls
docker network inspect uniticket_default

# connect your browser to http://172.18.0.1:8000 ...

# update a service with a new image (HA failed, 5 seconds od downtime registered here... still need to implement an health check)
docker service update --image uniticket:v1.2 --health-cmd "curl --fail http://localhost:8000/ || exit 1" --health-interval=5s --health-timeout=3s --health-retries=2 uniticket
````


Production Setup
----------------

After the following actions being made, copy and adapt the production configurations that you found in `uwsgi_setup/` folder.

````
apt install python3-dev python3-pip
pip3 install virtualenv
virtualenv -ppython3 uniticket.env
source uniticket.env/bin/activate
git clone https://github.com/UniversitaDellaCalabria/uniTicket.git uniticket
cd uniticket
pip3 install -r requirements.txt
pip3 install uwsgi

sudo apt install mariadb-server libmariadbclient-dev
sudo apt install poppler-utils xmlsec1
sudo apt install supervisor

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

./manage.py migrate
./manage.py collectstatic
./manage.py createsuperuser
./manage.py runserver

# if everything works, the big part is done!
````
