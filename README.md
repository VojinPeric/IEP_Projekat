# COMMAND MAP

## Venv initialization

### create the venv

python3 -m venv venv

### activate it

source venv/bin/activate
venv\Scripts\activate.bat
venv\Scripts\Activate.ps1
source venv/Scripts/activate
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

### upgrade pip

pip install --upgrade pip

### install dependencies

pip install -r requirements.txt

### check version of dep

pip index versions <dep_name>

## Docker

### Build

docker build -t <image_name_version>(iep-auth-migration:1.0) -f <filepath></filepath>(docker_files/auth/migration.dockerfile) .

### Quick build from project root

docker build -f docker_files/auth/migration.dockerfile -t iep-auth-migration:1.0 .
docker build -f docker_files/auth/authorization.dockerfile -t iep-auth:1.0 .
docker build -f docker_files/service/employee.dockerfile -t iep-employee:1.0 .
docker build -f docker_files/service/director.dockerfile -t iep-director:1.0 .
docker build -f docker_files/service/vote_listener.dockerfile -t iep-vote-listener:1.0 .

### Run

docker run <image_name_version>

### Compose

docker compose -f docker_files/auth/docker_compose.yaml up
docker compose -f docker_files/auth/docker_compose.yaml down (-v)

## Kubernetes (Docker Desktop)

### Context

kubectl config get-contexts                        # list available contexts
kubectl config use-context docker-desktop           # switch to Docker Desktop's built-in cluster
kubectl cluster-info                                # confirm the API server is reachable

### Apply (run in order, wait for each to be ready before the next)

kubectl apply -f kubernetes/00_config.yaml                 # secrets + configmaps first, everything else reads from these
kubectl apply -f kubernetes/auth/01_db.yaml                         # mysql pv/pvc/deployment/service
kubectl apply -f kubernetes/auth/02_migration.yaml                  # one-shot Job, only after mysql pod is Ready
kubectl apply -f kubernetes/auth/03_app.yaml                        # auth app deployment + LoadBalancer service
kubectl apply -f kubernetes/service/01_db_redis_provider.yaml       # mongo/redis/ganache
kubectl apply -f kubernetes/service/02_app.yaml                     # employee/director/vote-listener

### Dry run before applying (catches schema errors without creating anything)

kubectl apply --dry-run=client -f <file></file>            # validates locally
kubectl apply --dry-run=server -f <file></file>             # validates against the live API server

### Watching things come up

kubectl get pods                                    # -w to keep watching (Ctrl+C to stop)
kubectl get pods -w
kubectl get deployments
kubectl get services                                 # LoadBalancer EXTERNAL-IP shows as localhost on Docker Desktop
kubectl get pvc                                      # check PersistentVolumeClaim is Bound, not Pending
kubectl get jobs                                     # for the migration Job specifically

### Debugging a pod that's stuck/crashing

kubectl describe pod <pod-name></pod>                      # Events section at the bottom is usually the answer
kubectl logs <pod-name></pod>                              # stdout/stderr of the container
kubectl logs <pod-name></pod> -f                           # follow (tail -f style)
kubectl logs <pod-name></pod> --previous                   # logs from before the last crash/restart
kubectl logs -l app=director                         # logs by label instead of exact pod name (handy with replicas)

### Getting a shell inside a running pod

kubectl exec -it <pod-name></pod> -- /bin/bash             # or /bin/sh if bash isn't in the image
kubectl exec -it <pod-name></pod> -- env                   # quick check that ConfigMap/Secret env vars actually landed

### Port-forwarding to reach something without a LoadBalancer

kubectl port-forward svc/mongo-db-service 27017:27017
kubectl port-forward svc/redis-service 6379:6379

### Scaling

kubectl scale deployment employee-deployment --replicas=5
kubectl get pods -l app=employee                     # confirm the new replica count

### Restarting a deployment (e.g. after pushing a new image build with the same tag)

kubectl rollout restart deployment director-deployment
kubectl rollout status deployment director-deployment

### Cleanup (reverse order, or just delete by file)

kubectl delete -f kubernetes/service/02_app.yaml
kubectl delete -f kubernetes/service/01_db_redis_provider.yaml
kubectl delete -f kubernetes/auth/03_app.yaml
kubectl delete -f kubernetes/auth/02_migration.yaml
kubectl delete -f kubernetes/auth/01_db.yaml
kubectl delete -f kubernetes/00_config.yaml
kubectl delete pv mongopv localpv                    # PersistentVolumes aren't namespaced/owned by the above, delete explicitly if reclaiming disk

### Wipe volumes for a fresh reset (deleting the PV/PVC above does NOT delete the data on disk, only the k8s objects)

kubectl apply -f kubernetes/reset-volumes.yaml                                            # runs a busybox Job per volume that rm -rf's the hostPath dir
kubectl wait --for=condition=complete job/wipe-mongo-data job/wipe-mysql-data --timeout=60s
kubectl delete -f kubernetes/reset-volumes.yaml

# now re-apply everything from the top (Apply section) for brand new empty databases

## Odbrana

Internet je dostupan samo prvih 30 minuta. Faza 1 i Faza 2 moraju da se zavrse u tom prozoru
(sve sto zahteva internet je namerno grupisano u Fazu 2). Sve posle Faze 2 — deploy, testovi,
brisanje, izmena koda, dodavanje potpuno novog Dockerfile-a i redeploy — radi bez interneta,
koliko god puta je potrebno. Kljucni trik: `docker_files/base.dockerfile` pravi lokalni image
`iep-base:1.0` koji vec ima `requirements.txt` instaliran; svi ostali Dockerfile-ovi (postojeci i
bilo koji novi koji napravis na odbrani) kreni od `FROM iep-base:1.0` umesto `FROM python:3.13-slim`
i vise uopste ne pozivaju pip — pa nemaju nikakvu šansu da pokusaju internet, bez obzira na Docker
build cache.

Ogranicenje ovog trika: `iep-base:1.0` sadrzi samo pakete koji su bili u `requirements.txt` u
trenutku kad je build-ovan (Faza 2). Ako na samoj odbrani dodas potpuno nov paket u
`requirements.txt` koji tada nije postojao, njega tu nece biti i taj build ce pući bez interneta —
za to nema resenja, paket fizicki mora odnekud da se preuzme. Takodje, ne diraj
`docker system prune -a` niti `docker rmi iep-base:1.0` posle Faze 2, jer se time brise upravo taj
image.

### Faza 1 — Setup projekata i klastera (ne zahteva internet ako su alati vec instalirani)

1. Unzip projekat (docker_files/kubernetes/src/utils/requirements.txt/README.md) na Desktop
2. PyCharm -> New Project -> Python -> otvoriti/kreirati u tom raspakovanom folderu
3. Kopirati sve fajlove iz zipa u taj projekat (ako New Project napravi prazan folder)
4. Unzip grader/test projekat na Desktop (posebno, u drugi folder)
5. PyCharm -> New Project -> Python -> otvoriti/kreirati u tom folderu
6. Kopirati sve fajlove iz test zipa u taj projekat
7. Pokrenuti Docker Desktop, sacekati da Docker daemon bude gore

docker info                                          # potvrda da daemon radi, ne samo da je app otvoren

8. U Docker Desktop -> Settings -> Kubernetes: ukljuciti Kubernetes (ovo pravi/pokrece kubeadm klaster) i sacekati zeleni status

kubectl config get-contexts                          # opciono, verovatno vec aktivan
kubectl config use-context docker-desktop            # opciono, samo ako kontekst nije vec ovaj
kubectl cluster-info                                 # potvrda da je API server dostupan
kubectl get nodes                                    # potvrda da je node Ready

### Faza 2 — Sve sto zahteva internet (raditi odmah, dok traje prvih 30 minuta)

# image-i koje kubernetes/*.yaml direktno povlaci (baze, ganache, busybox za reset-volumes.yaml)
docker pull mongo:7.0
docker pull redis:7.4
docker pull mysql:8.0
docker pull trufflesuite/ganache-cli:v6.12.2
docker pull busybox

# 1) base image - povlaci python:3.13-slim i BAKE-uje requirements.txt u njega, ovo je jedini
#    korak u celoj odbrani kom je pip install-u ikad potreban internet
docker build -f docker_files/base.dockerfile -t iep-base:1.0 .

# 2) svi servisni image-i sada kreću od iep-base:1.0 (vidi FROM u docker_files/**/*.dockerfile) -
#    ne zovu pip uopste, build-uj ih sada dok ima interneta da budu spremni, ali rade i offline
docker build -f docker_files/auth/migration.dockerfile -t iep-auth-migration:1.0 .
docker build -f docker_files/auth/authorization.dockerfile -t iep-auth:1.0 .
docker build -f docker_files/service/employee.dockerfile -t iep-employee:1.0 .
docker build -f docker_files/service/director.dockerfile -t iep-director:1.0 .
docker build -f docker_files/service/vote_listener.dockerfile -t iep-vote-listener:1.0 .
docker images | grep -E "iep|mongo|redis|mysql|ganache|busybox"    # provera da je svih 11 image-a lokalno

# venv + zavisnosti za sam projekat (ako treba lokalno van dockera, npr. za migrate.py)
cd project
python -m venv venv
source venv/bin/activate                             # venv\Scripts\Activate.ps1 na Windows-u
pip install --upgrade pip
pip install -r requirements.txt

# venv + zavisnosti za grader/test projekat (ovaj se pokrece samo lokalno, van Dockera,
# pa je dovoljno instalirati direktno u venv, bez wheelhouse-a)
cd ../iep_grader
python -m venv .venv
source .venv/bin/activate                            # .venv\Scripts\Activate.ps1 na Windows-u
pip install -r requirements-pytest.txt

### Faza 3 — Deploy na Kubernetes (offline, redosled bitan, cekati Ready pre sledeceg koraka)

kubectl apply -f kubernetes/00_config.yaml
kubectl apply -f kubernetes/auth/01_db.yaml
kubectl rollout status deployment authentication-db-deployment    # ceka da mysql bude Ready

kubectl apply -f kubernetes/auth/02_migration.yaml
kubectl wait --for=condition=complete job/authentication-db-migration --timeout=120s

kubectl apply -f kubernetes/auth/03_app.yaml
kubectl rollout status deployment authentication-deployment

kubectl apply -f kubernetes/service/01_db_redis_provider.yaml
kubectl rollout status deployment mongo-db-deployment
kubectl rollout status deployment redis-deployment
kubectl rollout status deployment ganache-deployment

kubectl apply -f kubernetes/service/02_app.yaml
kubectl rollout status deployment employee-deployment
kubectl rollout status deployment director-deployment
kubectl rollout status deployment vote-listener-deployment

kubectl get pods                                    # sve Running/Completed, 0 restarts
kubectl get services                                 # EXTERNAL-IP je localhost na Docker Desktop

# Ocekivani LoadBalancer portovi (iz kubernetes/*.yaml, koriste se u komandi za testove ispod):
#   authentication-service  -> http://127.0.0.1:5001
#   employee-service        -> http://127.0.0.1:5002
#   director-service        -> http://127.0.0.1:5003
#   ganache-service         -> http://127.0.0.1:8545

### Faza 4 — Pokretanje grading testova (offline, iz test projekta, posle Faze 3)

cd ../iep_grader
source .venv/bin/activate                            # ako vec nije aktivan

pytest -q --type all \
  --authentication-url http://127.0.0.1:5001 \
  --jwt-secret JWT_SECRET_KEY \
  --roles-field role --employee-role employee --director-role director \
  --with-authentication \
  --employee-url http://127.0.0.1:5002 \
  --director-url http://127.0.0.1:5003 \
  --with-blockchain --provider-url http://127.0.0.1:8545 \
  --wait-for-services \
  --grade-report-file grade_report.json

### Faza 5 — Izmena koda, novi Dockerfile i redeploy (offline, ponavljati po potrebi)

# a) izmena postojeceg servisa: rebuild samo tog image-a - i dalje offline, jer FROM iep-base:1.0
#    znaci da pip install uopste ne postoji u ovom Dockerfile-u
docker build -f docker_files/service/employee.dockerfile -t iep-employee:1.0 .
kubectl rollout restart deployment employee-deployment      # forsira nove pod-ove da uzmu novoizgradjen lokalni image
kubectl rollout status deployment employee-deployment

# b) potpuno nov Dockerfile za novi servis: prva linija mora biti "FROM iep-base:1.0", NE
#    "FROM python:3.13-slim", i ne sme da sadrzi "RUN pip install ..." - paketi su vec u base
#    image-u, pa ni ovakav, nikad ranije build-ovan Dockerfile ne zahteva internet

### Faza 6 — Rusenje svih komponenti sa klastera (offline, obrnut redosled od Faze 3)

kubectl delete -f kubernetes/service/02_app.yaml
kubectl delete -f kubernetes/service/01_db_redis_provider.yaml
kubectl delete -f kubernetes/auth/03_app.yaml
kubectl delete -f kubernetes/auth/02_migration.yaml
kubectl delete -f kubernetes/auth/01_db.yaml
kubectl delete -f kubernetes/00_config.yaml
kubectl delete pv mongopv localpv --ignore-not-found
kubectl get all                                      # provera da nista nije ostalo (samo kubernetes default service)
kubectl get pv,pvc                                   # provera da nema zaostalih volumena

# za prazne baze pre sledeceg apply-a, videti "Wipe volumes for a fresh reset" iznad

# Proveriti pred odbranu

Kako se puluje python image ili bilo koj drugi sa neta da se sacuva lokalno
Proveriti kompajliranje ugovora i kako to da uradim staticki ili dinamicki bez interneta (Pitaj praiza sta mu je bio problem)
Proveri Kubernetes deployment

