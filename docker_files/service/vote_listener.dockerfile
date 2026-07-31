FROM iep-base:1.0

RUN mkdir -p /opt/src/service/shared
RUN mkdir -p /opt/src/service/director

WORKDIR /opt/src

COPY src/service/shared/configuration.py ./service/shared/configuration.py
COPY src/service/shared/models.py ./service/shared/models.py
COPY src/service/shared/blockchain.py ./service/shared/blockchain.py
COPY src/service/shared/contracts ./service/shared/contracts
COPY src/service/director/vote_listener.py ./service/director/vote_listener.py

ENV PYTHONPATH=.

ENTRYPOINT ["python", "./service/director/vote_listener.py"]
