
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

# if you don't use unical templates or derivates create a symbolic link to a default base template
ln -s /absolute/path/DEV/uniTicket/env/lib/python3.8/site-packages/bootstrap_italia_template/templates/bootstrap-italia-base.html  templates/base-setup.html

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
