
Docker Image
------------

````
# please do not use standard distribution package
# apt install docker docker.io docker-compose

# use official docker repositories instead
apt install docker-ce docker-ce-cli containerd.io

cd uniTicket

# build the containers and run them
# sudo docker-compose up

# build without composer
sudo docker image build --tag uniticket:v2 .

# Run on localhost:8000
sudo docker run -t -i -p 8000:8000 --name uniticket uniticket:v2
````

Docker Container
----------------

````
sudo docker ps

# get state and id of containers
sudo docker container ls

# get a terminal into a running container
sudo docker container exec -it b075a1193428 /bin/bash

# list changed file in the container
sudo docker container diff b075a1193428
# install and mofiy things with apt/vi ...
# commit changes in a new image (don't do this is you haven't yet created a registry, see next chapter)
sudo docker container commit ab7e1c57b31a uniticket:v1.2

# backup and restore an image
sudo docker save uniticket:v1.2 -o uniticket.v1.2.docker.img
sudo docker image load -i uniticket.v1.2.docker.img

# resource live statistics about a container
sudo docker container stats b075a1193428

# inspect container environemnt
sudo docker container inspect b075a1193428

# display running processes in the container
sudo docker container top b075a1193428
````

Docker Swarm
------------
Single node Docker swarm [health check WiP]

````
# create the swam
sudo docker swarm init

# create a registry is swarm is composed by more then one node ...
# exec registry as an app on localhost
sudo docker run -d -p 5000:5000 --restart=always --name registry registry:2
# tag a local docker image by its uid in the registry
sudo docker tag 46c4806e5d61 localhost:5000/uniticket
# upload it
sudo docker push localhost:5000/uniticket

# create a service
sudo docker service create --name="uniticket" --publish 8000:8000/tcp --replicas 2 localhost:5000/uniticket

# see status
sudo docker service ps uniticket --no-trunc

# see wich network (gateway) is associated to the service
sudo docker network ls
sudo docker network inspect uniticket_default

# connect your browser to http://172.18.0.1:8000 ...

# update a service with a new image (HA failed, 5 seconds of downtime registered here... still need to implement an health check)
sudo docker service update --image uniticket:v1.2 --health-cmd "curl --fail http://localhost:8000/ || exit 1" --health-interval=5s --health-timeout=3s --health-retries=2 uniticket
````
