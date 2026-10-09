
Docker — Quick Start
--------------------

### 1. Prepare the project folder

```bash
git clone https://github.com/UniversitaDellaCalabria/uniTicket.git
cd uniTicket
cp .env.example .env        # then edit .env and set your DOMAIN
./docker-prepare.sh
```

`docker-prepare.sh` reads `DOMAIN` from `.env` (or from the first argument / environment)
and patches `CSRF_TRUSTED_ORIGINS` in the Django settings accordingly.

### 2a. HTTP only (development / local testing)

```bash
docker compose up --build
```

The application is available at `http://localhost:8000`.

Demo credentials (loaded from `dumps/example_conf.json`):

| Role     | Username | Password  |
|----------|----------|-----------|
| Manager  | user1    | secret1!  |
| Operator | user2    | secret2!  |
| User     | utente   | secret1!  |

Admin interface: `http://localhost:8000/admin_path`

### 2b. HTTPS with automatic certificate (production / public deployment)

Requires ports **80** and **443** reachable from the internet (Let's Encrypt HTTP-01 challenge).

```bash
docker compose -f docker-compose.yml -f docker-compose.https.yml up --build -d
```

[Caddy](https://caddyserver.com/) will obtain and renew a Let's Encrypt certificate automatically
for the domain specified in `.env`. No manual certificate management needed.

The application is available at `https://<your-domain>`.

> **Note:** Port 8000 remains reachable directly. For production, restrict it at the
> firewall / cloud security group level so all traffic goes through HTTPS.

### Updating

```bash
docker compose pull
docker compose -f docker-compose.yml -f docker-compose.https.yml up -d
```

---

Docker Image
------------

````
# pull the pre-built image
docker pull ghcr.io/universitadellacalabria/uniticket:latest

# or build locally
docker image build --tag uniticket:latest .

# run standalone (no compose)
docker run -t -i -p 8000:8000 --name uniticket uniticket:latest
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

# backup and restore an image
sudo docker save uniticket:v1.2 -o uniticket.v1.2.docker.img
sudo docker image load -i uniticket.v1.2.docker.img

# resource live statistics about a container
sudo docker container stats b075a1193428

# inspect container environment
sudo docker container inspect b075a1193428

# display running processes in the container
sudo docker container top b075a1193428
````

Docker Swarm
------------
Single node Docker swarm [health check WiP]

````
# create the swarm
sudo docker swarm init

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

# update a service with a new image
sudo docker service update --image uniticket:v1.2 --health-cmd "curl --fail http://localhost:8000/ || exit 1" --health-interval=5s --health-timeout=3s --health-retries=2 uniticket
````
