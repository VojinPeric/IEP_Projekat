FROM python:3.13-slim

RUN mkdir -p /opt/src/auth
RUN mkdir -p /opt/src/shared

WORKDIR /opt/src

COPY requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

COPY src/auth/application.py ./auth/application.py
COPY src/auth/api_endpoints.py ./auth/api_endpoints.py
COPY src/auth/configuration.py ./auth/configuration.py
COPY src/auth/models.py ./auth/models.py
COPY src/shared/credential_decorators.py ./shared/credential_decorators.py

ENV PYTHONPATH=.

ENTRYPOINT ["python", "./auth/application.py"]