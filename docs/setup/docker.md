# Docker

Questa sezione descrive come installare, configurare e gestire uniTicket utilizzando Docker, dalla configurazione rapida (Quick Start) alla gestione in Alta Affidabilità con Swarm.

### Avvio Rapido (Quick Start)

Per una demo o un'installazione rapida, segui questi passaggi:

#### Preparazione Host

assicurati di installare Docker dai repository ufficiali e docker-compose via pip:

```
sudo pip install docker-compose
```

#### Installazione e Configurazione

Pull dell'immagine ufficiale:

```
docker pull ghcr.io/UniversitaDellaCalabria/uniTicket:latest
```

#### Preparazione cartelle e asset

Esegui lo script bash per generare la struttura necessaria:

```
bash docker-prepare.sh
```

#### Personalizzazione

Modifica i file in uniticket/uni_ticket_project/settingslocal.py.  
Se necessario, personalizza i dati contenuti in examples-docker/ (dump JSON).

#### Avvio dello stack

```
sudo docker-compose up -d
```

#### Accesso

Punta il browser su http://localhost:8000/ ed effettua la prima autenticazione.

### Gestione Immagini e Container

In assenza di orchestratori complessi, puoi gestire uniTicket manualmente per test o backup.

* Build manuale: ```sudo docker image build --tag uniticket:v2 .```;

* Run rapido: ```sudo docker run -t -i -p 8000:8000 --name uniticket uniticket:v2```;

* Backup (Export): ```sudo docker save uniticket:v1.2 -o uniticket.v1.2.docker.img```;

* Ripristino (Import): ```sudo docker image load -i uniticket.v1.2.docker.img```.

### Docker Swarm (Alta Affidabilità)

Per ambienti di produzione, l'integrazione con Docker Swarm garantisce che uniTicket sia sempre disponibile anche in caso di guasto di un nodo.

#### Setup del Registro Locale

Swarm richiede che le immagini siano depositate in un registro accessibile:

* Avvia il registro: 
```sudo docker run -d -p 5000:5000 --name registry registry:2```

* Tag & Push:
```
sudo docker tag uniticket:latest localhost:5000/uniticket
sudo docker push localhost:5000/uniticket
```

#### Servizio Scalabile e Rolling Updates

* Creazione Servizio (2 repliche):

```
sudo docker service create --name="uniticket" --publish 8000:8000/tcp --replicas 2 localhost:5000/uniticket
```

* Aggiornamento Zero-Downtime:

L'update viene eseguito solo se l'Health Check (il comando curl sulla home) ha successo:

```
sudo docker service update --image uniticket:v1.2 --health-cmd "curl --fail http://localhost:8000/ || exit 1" --health-interval=5s uniticket
```

!!! warning "Persistenza dei Dati"
    I container sono volatili. Assicurati che il database PostgreSQL e la cartella dei media (allegati dei ticket) siano montati su volumi esterni o database gestiti fuori dallo swarm. In caso contrario, i dati andranno persi al riavvio del servizio.