FROM python:3.13-slim

RUN mkdir -p /opt/src/service/shared
RUN mkdir -p /opt/src/service/director

WORKDIR /opt/src

COPY requirements.txt ./requirements.txt

RUN pip install -r ./requirements.txt

COPY src/service/shared/configuration.py ./service/shared/configuration.py
COPY src/service/shared/models.py ./service/shared/models.py
COPY src/service/shared/blockchain.py ./service/shared/blockchain.py
COPY src/service/shared/contracts ./service/shared/contracts
COPY src/service/director/vote_listener.py ./service/director/vote_listener.py

ENV PYTHONPATH=.

ENTRYPOINT ["python", "./service/director/vote_listener.py"]
