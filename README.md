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
docker build -t <image_name_version>(iep-auth-migration:1.0) -f <filepath>(docker_files/auth/migration.dockerfile) .

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
kubectl apply --dry-run=client -f <file>            # validates locally
kubectl apply --dry-run=server -f <file>             # validates against the live API server

### Watching things come up
kubectl get pods                                    # -w to keep watching (Ctrl+C to stop)
kubectl get pods -w
kubectl get deployments
kubectl get services                                 # LoadBalancer EXTERNAL-IP shows as localhost on Docker Desktop
kubectl get pvc                                      # check PersistentVolumeClaim is Bound, not Pending
kubectl get jobs                                     # for the migration Job specifically

### Debugging a pod that's stuck/crashing
kubectl describe pod <pod-name>                      # Events section at the bottom is usually the answer
kubectl logs <pod-name>                              # stdout/stderr of the container
kubectl logs <pod-name> -f                           # follow (tail -f style)
kubectl logs <pod-name> --previous                   # logs from before the last crash/restart
kubectl logs -l app=director                         # logs by label instead of exact pod name (handy with replicas)

### Getting a shell inside a running pod
kubectl exec -it <pod-name> -- /bin/bash             # or /bin/sh if bash isn't in the image
kubectl exec -it <pod-name> -- env                   # quick check that ConfigMap/Secret env vars actually landed

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

