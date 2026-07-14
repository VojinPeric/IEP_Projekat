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