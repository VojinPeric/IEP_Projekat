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

### Run
docker run <image_name_version>

### Compose
docker compose -f docker_files/auth/docker_compose.yaml up
docker compose -f docker_files/auth/docker_compose.yaml down (-v)

