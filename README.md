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
docker pull python:3.13-slim
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
docker images | grep -E "iep|mongo|redis|mysql|ganache|busybox"   

# venv + zavisnosti za sam projekat (ako treba lokalno van dockera, npr. za migrate.py)
cd project
python -m venv venv
source venv/bin/activate                            
pip install --upgrade pip
pip install -r requirements.txt

# venv + zavisnosti za grader/test projekat (ovaj se pokrece samo lokalno, van Dockera,
# pa je dovoljno instalirati direktno u venv, bez wheelhouse-a)
prvo dodati setuptools<81 u requirements-pytest.txt

cd ../iep_grader
python -m venv .venv
source .venv/bin/activate                           
pip install -r requirements-pytest.txt

# venv + zavisnosti za utils/compile_proposal.py (solcx nije i ne sme biti u project/requirements.txt -
# nijedan servis ga ne koristi u runtime-u, samo ovaj rucni compile korak; poseban venv drzi ga odvojeno)
cd ../project
python -m venv utils/venv
source utils/venv/bin/activate                      
pip install -r utils/requirements.txt
python -c "import solcx; solcx.install_solc('0.8.24')"  
deactivate

### Faza 3 — Deploy na Kubernetes (offline, redosled bitan, cekati Ready pre sledeceg koraka)

kubectl apply -f kubernetes/00_config.yaml
kubectl apply -f kubernetes/auth/01_db.yaml
kubectl rollout status deployment authentication-db-deployment    

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

kubectl get pods                                    
kubectl get services                                 

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

# c) izmena ugovora (src/service/shared/contracts/Proposal.sol) i regeneracija Proposal.json -
#    offline je jer je solc 0.8.24 vec kesiran u Fazi 2 preko solcx.install_solc(...)
source utils/venv/bin/activate                       # utils\venv\Scripts\Activate.ps1 na Windows-u
python utils/compile_proposal.py
deactivate
docker build -f docker_files/service/director.dockerfile -t iep-director:1.0 .
docker build -f docker_files/service/vote_listener.dockerfile -t iep-vote-listener:1.0 .
kubectl rollout restart deployment director-deployment vote-listener-deployment
kubectl rollout status deployment director-deployment
kubectl rollout status deployment vote-listener-deployment

### Faza 6 — Rusenje svih komponenti sa klastera (offline, obrnut redosled od Faze 3)

kubectl delete -f kubernetes/service/02_app.yaml
kubectl delete -f kubernetes/service/01_db_redis_provider.yaml
kubectl delete -f kubernetes/auth/03_app.yaml
kubectl delete -f kubernetes/auth/02_migration.yaml
kubectl delete -f kubernetes/auth/01_db.yaml
kubectl delete -f kubernetes/00_config.yaml
kubectl delete pv mongopv localpv --ignore-not-found
kubectl get all                                      
kubectl get pv,pvc                                   

# za prazne baze pre sledeceg apply-a, videti "Wipe volumes for a fresh reset" iznad

## Flask / Mongo / Redis

### Flask — kako ulaze parametri u funkciju rute

- deo putanje (npr `/employee/<id>`) -> stize kao argument funkcije, definise se u `@app.route("/employee/<id>")` i mora da se navede isto ime u potpisu funkcije
- posle znaka pitanja u URL-u (npr `?status=active`) -> cita se iz objekta koji drzi sve query parametre, uvek string, ako ga nema treba dati podrazumevanu vrednost umesto da puca

  status = request.args.get("status", "default_vrednost")
- iz tela zahteva (POST/PUT, JSON) -> parsira se poseban helper koji telo zahteva pretvara u dict, treba paziti da klijent salje `Content-Type: application/json`, inace parsiranje vraca None
- headeri (npr Authorization token) -> takodje dostupni preko posebnog recnika na request objektu, kljucevi nisu case-sensitive

Redosled provere kad nesto ne stize: prvo da li je uopste u odgovarajucem delu zahteva (Postman/curl -> proveriti sta se salje), pa da li se u kodu cita sa ispravnog mesta (path vs query vs body).

Povratna vrednost rute:
- moze biti obican string/dict (Flask ga sam pretvori u JSON i vrati 200)
- moze se vratiti tuple (telo, status_kod) da se eksplicitno postavi kod (npr 201, 400, 404)
- za greske najbolje odmah vratiti dict sa porukom + status kod, ne ostavljati da pukne 500 bez objasnjenja

### MongoDB — operacije nad kolekcijom

Osnovna podela: operacije rade nad citavim dokumentima (insert/find/delete cele stavke) ili nad poljima unutar dokumenta (update operatori). `col` = referenca na kolekciju (npr `db["employees"]`).

- ubacivanje jednog dokumenta / vise njih odjednom -> jedna komanda za jedan dict, druga za listu dict-ova

  col.insert_one({"name": "Pera", "age": 30})
  col.insert_many([{"name": "Pera"}, {"name": "Mika"}])

- pretraga -> filter je dict sa uslovima; jedna komanda vraca prvi poklapajuci dokument, druga vraca sve (kroz njih se onda iterira)

  col.find_one({"name": "Pera"})
  for doc in col.find({"age": {"$gt": 18}}):
      ...

- filtriranje po ugnjezdenom polju -> koristi se tackasta notacija u kljucu filtera (npr `"address.city"`), Mongo sam zna da udje unutra

  col.find({"address.city": "Nis"})

- brisanje -> jedna komanda za prvi poklapajuci dokument, druga za sve koji se poklapaju sa filterom

  col.delete_one({"name": "Pera"})
  col.delete_many({"age": {"$lt": 18}})

- izmena postojeceg dokumenta -> filter + operator; ako se ne stavi operator nego se posalje ceo novi dokument, on ce zameniti stari u potpunosti (obratiti paznju, to je razlika izmedju "izmeni polje" i "zameni dokument")

  col.update_one({"name": "Pera"}, {"$set": {"age": 31}})
  col.replace_one({"name": "Pera"}, {"name": "Pera", "age": 31})

- operator za postavljanje/menjanje vrednosti polja (i za dodavanje novog polja ako ne postoji) -> `$set`
- operator za brisanje polja iz dokumenta (ne brise ceo dokument, samo taj kljuc) -> `$unset`

  col.update_one({"name": "Pera"}, {"$unset": {"age": ""}})

- operator za uvecanje/umanjenje brojcanog polja za neku vrednost -> `$inc`

  col.update_one({"name": "Pera"}, {"$inc": {"age": 1}})

- rad sa listama unutar dokumenta (operator `$push` dodaje, `$pull` uklanja, `$pop` skida sa kraja/pocetka):

  col.update_one({"name": "Pera"}, {"$push": {"hobiji": "sah"}})
  col.update_one({"name": "Pera"}, {"$push": {"hobiji": {"$each": ["sah", "fudbal"]}}})
  col.update_one({"name": "Pera"}, {"$pull": {"hobiji": "sah"}})
  col.update_one({"name": "Pera"}, {"$pop": {"hobiji": 1}})   # 1 = poslednji, -1 = prvi

  provera da li lista sadrzi vrednost ide direktno u filter: col.find({"hobiji": "sah"})

- da li update pogodi vise dokumenata odjednom ili samo jedan -> zavisi koja se varijanta komande pozove (`update_one` vs `update_many`), ne od filtera samog
- kad dokument ne postoji a zeli se da se napravi ako ga nema (umesto rucne provere pa insert) -> `upsert=True` prosledjen kao dodatni argument update poziva

  col.update_one({"name": "Pera"}, {"$set": {"age": 31}}, upsert=True)

Sortiranje/limit/skip pri citanju -> lancaju se na rezultat pretrage, korisno za paginaciju:

  col.find().sort("age", -1).skip(10).limit(5)

### MongoDB — aggregate pipeline

`aggregate` uzima listu koraka (dict-ova), svaki korak uzima izlaz prethodnog kao svoj ulaz. Redosled koraka je bitan (npr `$match` staviti sto ranije da se smanji broj dokumenata pre skupljih koraka).

  col.aggregate([
      {"$match": {"status": "active"}},
      {"$group": {"_id": "$department", "total": {"$sum": 1}}},
  ])

- `$match` -> filtrira dokumente, ista sintaksa uslova kao kod `find` filtera, po pravilu prvi korak u pipeline-u

  {"$match": {"age": {"$gte": 18}}}

- `$group` -> pravi grupe po nekom polju (`_id` u ovom koraku = po cemu se grupise) i racuna agregat po grupi

  {"$group": {"_id": "$department", "prosek_plata": {"$avg": "$salary"}, "broj": {"$sum": 1}}}

  akumulatori koji resavaju vecinu slucajeva: `$sum` (broj/zbir), `$avg`, `$min`, `$max`, `$push` (skupi vrednosti u listu), `$addToSet` (isto ali bez duplikata), `$first`/`$last`

- `$unwind` -> "razlista" polje koje je niz, tako da dobijes po jedan dokument za svaki element niza (obavezno pre `$group` ako se grupise po necemu iz te liste)

  {"$unwind": "$hobiji"}

- `$project` -> bira koja polja idu dalje / racuna novo polje u letu, `1` = zadrzi, `0` = izbaci

  {"$project": {"name": 1, "godina_rodjenja": {"$subtract": [2026, "$age"]}, "_id": 0}}

- `$addFields` -> kao `$project` ali samo dodaje/menja polja, ne mora eksplicitno da nabraja sve ostale koje zeli da zadrzi

  {"$addFields": {"pun_naziv": {"$concat": ["$ime", " ", "$prezime"]}}}

- `$sort` / `$limit` / `$skip` -> isto znacenje kao kod obicnog `find`, samo kao koraci u pipeline-u

  {"$sort": {"total": -1}}
  {"$limit": 10}

- `$count` -> vrati samo broj dokumenata koji su stigli do tog koraka (zamena za `$group` + `$sum: 1` kad ne treba nista drugo)

  {"$count": "ukupno"}

- `$lookup` -> "join" sa drugom kolekcijom, poveze dokumente po polju i ubaci rezultat kao listu u novo polje

  {"$lookup": {
      "from": "departments",
      "localField": "department_id",
      "foreignField": "_id",
      "as": "department_info",
  }}

  posle `$lookup` rezultat u `department_info` je uvek lista (i kad ima samo jedno poklapanje) -> cesto se doda `$unwind` odmah posle da se raspakuje u obican dokument.

### Redis — kljucevi i tipovi

Sve je kljuc -> vrednost, ali vrednost moze biti razlicitog tipa; komande se biraju prema tipu koji se koristi. `r` = konekcija (npr `redis.Redis(host=..., port=6379)`).

- string (najprostiji tip, cesto broj ili JSON kao tekst) -> postavljanje vrednosti, citanje, uvecanje/umanjenje broja za 1 ili vise

  r.set("visits", 1)
  r.get("visits")
  r.incr("visits")          # +1
  r.incrby("visits", 5)     # +5
  r.decr("visits")          # -1

- postavljanje vrednosti sa isticanjem (TTL) -> ili odmah pri upisu, ili naknadno na postojeci kljuc; korisno za keš/sesije

  r.set("session:123", "token_vrednost", ex=3600)   # ex = sekunde do isteka
  r.expire("session:123", 3600)                      # naknadno na postojeci kljuc

- provera koliko jos kljuc ima da zivi, ili da se ucini trajnim (ukloni TTL)

  r.ttl("session:123")
  r.persist("session:123")

- hash (kao mali recnik unutar jednog kljuca, pogodno za "objekat" tipa korisnik) -> postavljanje jednog polja, postavljanje vise polja odjednom, citanje jednog polja ili svih polja

  r.hset("user:1", "name", "Pera")
  r.hset("user:1", mapping={"name": "Pera", "age": 30})
  r.hget("user:1", "name")
  r.hgetall("user:1")

- lista (redosled bitan, moze duplikate) -> dodavanje na pocetak ili kraj, citanje opsega elemenata, uklanjanje sa pocetka/kraja

  r.lpush("queue", "a")      # na pocetak
  r.rpush("queue", "b")      # na kraj
  r.lrange("queue", 0, -1)   # ceo opseg
  r.lpop("queue")
  r.rpop("queue")

- set (jedinstvene vrednosti, redosled nebitan) -> dodavanje clana, provera pripadnosti, uklanjanje clana, broj clanova

  r.sadd("tags", "python")
  r.sismember("tags", "python")
  r.srem("tags", "python")
  r.scard("tags")

- sorted set (kao set ali svaki clan ima skor po kome se sortira) -> dodavanje clana sa skorom, citanje po rangu ili po skoru, korisno za leaderboard/rangiranje

  r.zadd("leaderboard", {"Pera": 100})
  r.zrange("leaderboard", 0, -1, withscores=True)   # po rangu (redosledu)
  r.zrangebyscore("leaderboard", 50, 150)            # po opsegu skora

- brisanje kljuca (bilo kog tipa) -> ista komanda za sve tipove

  r.delete("user:1")

- provera da li kljuc postoji uopste, i koji je tip vrednosti pod njim

  r.exists("user:1")
  r.type("user:1")

Kad nesto ne radi kako treba: najcesci uzrok je pokusaj pozivanja komande za pogresan tip (npr lista-komanda nad hash kljucem), Redis ce vratiti gresku tipa umesto da nesto uradi.

