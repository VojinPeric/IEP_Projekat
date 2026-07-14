FROM python:3.13-slim

RUN mkdir -p /opt/src/auth
WORKDIR /opt/src/auth

COPY requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

COPY src/auth/migrate.py ./migrate.py
COPY src/auth/configuration.py ./configuration.py
COPY src/auth/models.py ./models.py

ENTRYPOINT ["python", "./migrate.py"]
